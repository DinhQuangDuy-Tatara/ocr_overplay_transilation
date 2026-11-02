from PIL import Image
from ocr_overlay.models import OCRLine


class PaddleOCRAdapter:
    """Lazy adapter for PaddleOCR 2.x result format (Korean by default)."""

    def __init__(self, *, use_angle_cls: bool = True, min_confidence: float = 0.0):
        self._engines = {}
        self.use_angle_cls = use_angle_cls
        self.min_confidence = min_confidence

    def _engine(self, language: str):
        if language not in self._engines:
            try:
                from paddleocr import PaddleOCR
            except ImportError as exc:
                raise RuntimeError(
                    "Chưa cài PaddleOCR. Hãy cài extra OCR theo README."
                ) from exc
            lang = {"ko": "korean", "en": "en", "ch": "ch"}.get(language, language)
            try:
                engine = PaddleOCR(use_angle_cls=self.use_angle_cls, lang=lang, show_log=False)
            except TypeError:  # Compatibility with PaddleOCR releases changing constructor args
                engine = PaddleOCR(use_angle_cls=self.use_angle_cls, lang=lang)
            self._engines[language] = engine
        return self._engines[language]

    @staticmethod
    def _parse_legacy(raw):
        output = []
        for page in raw or []:
            for entry in page or []:
                try:
                    polygon, (text, confidence) = entry
                    points = tuple((int(round(p[0])), int(round(p[1]))) for p in polygon)
                    if not points or not str(text).strip():
                        continue
                    xs, ys = zip(*points)
                    output.append(OCRLine(
                        str(text).strip(),
                        (min(xs), min(ys), max(xs), max(ys)),
                        float(confidence), points
                    ))
                except (TypeError, ValueError, IndexError):
                    continue
        return output

    def recognize(self, image: Image.Image, language: str = "ko") -> list[OCRLine]:
        if not isinstance(image, Image.Image):
            raise TypeError("OCR input phải là PIL.Image.Image")
        if image.width <= 0 or image.height <= 0:
            raise ValueError("Ảnh đầu vào rỗng")
        import numpy as np
        rgb = image.convert("RGB")
        raw = self._engine(language).ocr(np.asarray(rgb), cls=self.use_angle_cls)
        lines = self._parse_legacy(raw)
        return [line for line in lines if line.confidence >= self.min_confidence]
