from pathlib import Path
from PIL import Image


class ImageFileCapture:
    """Deterministic image source for the first OCR/pipeline milestone."""

    def capture(self, path: Path) -> Image.Image:
        if not path.is_file():
            raise FileNotFoundError(path)
        with Image.open(path) as image:
            return image.convert("RGB")
