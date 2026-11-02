from PIL import Image
from ocr_overlay.models import OCRLine
from ocr_overlay.pipeline.service import OCRTranslationPipeline
from ocr_overlay.storage.cache import TranslationCache


class FakeOCR:
    def recognize(self, image, language):
        return [OCRLine("안녕하세요", (1, 2, 20, 10), 0.99)]


class FakeTranslator:
    version = "fake-v1"
    def __init__(self): self.calls = 0
    def translate(self, text, source, target):
        self.calls += 1
        return "Xin chào"


def test_pipeline_translation_cache_and_polygon(tmp_path):
    translator = FakeTranslator()
    pipeline = OCRTranslationPipeline(
        FakeOCR(), translator, TranslationCache(tmp_path / "cache.sqlite")
    )
    image = Image.new("RGB", (30, 20), "white")
    first = pipeline.process(image, "ko", "vi")
    second = pipeline.process(image, "ko", "vi")
    assert first[0].translation == second[0].translation == "Xin chào"
    assert translator.calls == 1
    assert first[0].polygon == ((1, 2), (20, 2), (20, 10), (1, 10))
