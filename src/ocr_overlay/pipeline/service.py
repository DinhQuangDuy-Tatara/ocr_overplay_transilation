from PIL import Image
from ocr_overlay.models import TranslatedLine
from ocr_overlay.ocr.base import OCRProvider
from ocr_overlay.storage.cache import TranslationCache
from ocr_overlay.translation.base import TranslationProvider


class OCRTranslationPipeline:
    def __init__(self, ocr: OCRProvider, translator: TranslationProvider, cache: TranslationCache):
        self.ocr = ocr
        self.translator = translator
        self.cache = cache

    def process(self, image: Image.Image, source: str, target: str) -> list[TranslatedLine]:
        if not isinstance(image, Image.Image):
            raise TypeError("Pipeline yêu cầu đầu vào PIL.Image.Image")
        if image.width <= 0 or image.height <= 0:
            raise ValueError("Ảnh đầu vào rỗng")
        results = []
        for line in self.ocr.recognize(image.convert("RGB"), source):
            if not line.text.strip():
                continue
            version = getattr(self.translator, "version", type(self.translator).__name__)
            key = self.cache.make_key(line.text, source, target, version)
            translation = self.cache.get(key)
            if translation is None:
                translation = self.translator.translate(line.text, source, target)
                if not isinstance(translation, str) or not translation.strip():
                    raise ValueError("Translation provider trả về bản dịch rỗng")
                self.cache.put(key, translation)
            results.append(TranslatedLine(
                line.text, translation, line.box, line.confidence, line.effective_polygon
            ))
        return results
