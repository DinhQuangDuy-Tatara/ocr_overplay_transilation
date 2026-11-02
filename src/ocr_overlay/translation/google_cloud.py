import json
import os
import urllib.error
import urllib.parse
import urllib.request


class TranslationError(RuntimeError):
    pass


class TranslationProviderError(TranslationError):
    pass


class TranslationTimeout(TranslationError):
    pass


class GoogleCloudTranslationProvider:
    """Official Google Cloud Translation v2 REST API provider."""

    version = "google-cloud-v2"

    def __init__(self, api_key: str | None = None, timeout: float = 10.0):
        self.api_key = api_key or os.getenv("GOOGLE_CLOUD_TRANSLATE_API_KEY")
        self.timeout = timeout
        if not self.api_key:
            raise ValueError(
                "Thiếu GOOGLE_CLOUD_TRANSLATE_API_KEY. Xem README để cấu hình."
            )
        if timeout <= 0:
            raise ValueError("timeout phải lớn hơn 0")

    def translate(self, text: str, source: str, target: str) -> str:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Văn bản cần dịch không được để trống")
        params = urllib.parse.urlencode({"key": self.api_key})
        url = f"https://translation.googleapis.com/language/translate/v2?{params}"
        body = json.dumps({
            "q": text, "source": source, "target": target, "format": "text"
        }).encode("utf-8")
        request = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except TimeoutError as exc:
            raise TranslationTimeout("Google Translation API timeout") from exc
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            if exc.code == 429:
                raise TranslationProviderError("Google Translation API rate limit (429)") from exc
            raise TranslationProviderError(
                f"Google Translation API HTTP {exc.code}: {detail}"
            ) from exc
        except (urllib.error.URLError, OSError) as exc:
            if isinstance(getattr(exc, "reason", None), TimeoutError):
                raise TranslationTimeout("Google Translation API timeout") from exc
            raise TranslationProviderError(f"Không thể kết nối Translation API: {exc}") from exc
        try:
            translated = payload["data"]["translations"][0]["translatedText"]
        except (KeyError, IndexError, TypeError) as exc:
            raise TranslationProviderError("Phản hồi Google Translation API không hợp lệ") from exc
        if not isinstance(translated, str) or not translated.strip():
            raise TranslationProviderError("Google Translation API trả về bản dịch rỗng")
        return translated
