from typing import Protocol
from PIL import Image
from ocr_overlay.models import OCRLine


class OCRProvider(Protocol):
    def recognize(self, image: Image.Image, language: str) -> list[OCRLine]: ...
