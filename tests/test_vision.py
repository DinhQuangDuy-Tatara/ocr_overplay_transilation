from PIL import Image
from ocr_overlay.models import TranslatedLine
from ocr_overlay.vision.processing import inpaint_text_regions, render_translations


def line():
    return TranslatedLine("안녕", "Xin chào", (10, 10, 70, 40), 0.9,
                          ((10, 10), (70, 10), (70, 40), (10, 40)))


def test_render_translations_returns_same_size_rgb():
    image = Image.new("RGB", (100, 60), "white")
    result = render_translations(image, [line()])
    assert result.size == image.size
    assert result.mode == "RGB"
    assert result.tobytes() != image.tobytes()


def test_inpaint_disabled_returns_copy():
    image = Image.new("RGB", (20, 20), "white")
    result = inpaint_text_regions(image, [line()], enabled=False)
    assert result is not image
    assert result.tobytes() == image.tobytes()


def test_inpaint_enabled_preserves_dimensions_and_source():
    image = Image.new("RGB", (100, 60), "white")
    original = image.tobytes()
    result = inpaint_text_regions(image, [line()], enabled=True)
    assert result.size == image.size
    assert image.tobytes() == original
