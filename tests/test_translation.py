import json
from unittest.mock import patch
from ocr_overlay.translation.google_cloud import (
    GoogleCloudTranslationProvider, TranslationProviderError
)


class FakeResponse:
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self):
        return json.dumps({"data": {"translations": [{"translatedText": "Xin chào"}]}}).encode()


def test_google_cloud_provider_posts_and_parses():
    provider = GoogleCloudTranslationProvider("test-key")
    with patch("urllib.request.urlopen", return_value=FakeResponse()) as mocked:
        assert provider.translate("안녕", "ko", "vi") == "Xin chào"
    assert mocked.call_args.kwargs["timeout"] == 10.0


def test_provider_requires_api_key():
    import pytest
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError):
            GoogleCloudTranslationProvider()


def test_cache_key_can_include_provider_version():
    from ocr_overlay.storage.cache import TranslationCache
    assert TranslationCache.make_key("x", "ko", "vi", "a") != TranslationCache.make_key("x", "ko", "vi", "b")
