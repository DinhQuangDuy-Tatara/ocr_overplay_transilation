from typing import Protocol


class TranslationProvider(Protocol):
    def translate(self, text: str, source: str, target: str) -> str: ...
