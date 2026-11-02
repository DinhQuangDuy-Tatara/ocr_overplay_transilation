import argparse
import os
from pathlib import Path
from PIL import Image

from ocr_overlay.capture.image_file import ImageFileCapture
from ocr_overlay.ocr.paddle_adapter import PaddleOCRAdapter
from ocr_overlay.pipeline.service import OCRTranslationPipeline
from ocr_overlay.storage.cache import TranslationCache
from ocr_overlay.translation.google_cloud import GoogleCloudTranslationProvider
from ocr_overlay.vision.processing import process_translated_image


def main() -> None:
    parser = argparse.ArgumentParser(description="Real-Time Screen Translator")
    parser.add_argument("--image", type=Path, help="Process an image file (debug mode)")
    parser.add_argument("--source", default="ko")
    parser.add_argument("--target", default="vi")
    parser.add_argument("--output", type=Path, default=Path("rtst_output.png"))
    parser.add_argument("--no-inpaint", action="store_true")
    parser.add_argument("--show-overlay", action="store_true", help="Show processed image in Qt overlay")
    args = parser.parse_args()

    if not args.image:
        from ocr_overlay.ui.app import main as gui_main
        raise SystemExit(gui_main())

    image = ImageFileCapture().capture(args.image)
    cache = TranslationCache(Path.home() / ".cache/rtst/translations.sqlite3")
    translator = GoogleCloudTranslationProvider(
        timeout=float(os.getenv("RTST_TRANSLATION_TIMEOUT", "12"))
    )
    pipeline = OCRTranslationPipeline(PaddleOCRAdapter(), translator, cache)
    results = pipeline.process(image, args.source, args.target)
    for item in results:
        print(f"{item.text} -> {item.translation} @ {item.box} ({item.confidence:.3f})")
    output = process_translated_image(image, results, remove_original=not args.no_inpaint)
    output.save(args.output)
    print(f"Saved: {args.output}")
    if args.show_overlay:
        from ocr_overlay.ui.overlay import show_image_overlay
        show_image_overlay(output, 0, 0)


if __name__ == "__main__":
    main()
