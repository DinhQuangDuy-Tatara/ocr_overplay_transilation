from pathlib import Path
from ocr_overlay.storage.cache import TranslationCache


def test_cache_round_trip(tmp_path: Path):
    cache = TranslationCache(tmp_path / "cache.sqlite3")
    key = cache.make_key("안녕", "ko", "vi")
    assert cache.get(key) is None
    cache.put(key, "Xin chào")
    assert cache.get(key) == "Xin chào"


def test_cache_key_uses_languages():
    assert TranslationCache.make_key("text", "ko", "vi") != TranslationCache.make_key("text", "en", "vi")
