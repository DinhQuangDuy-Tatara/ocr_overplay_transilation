from dataclasses import dataclass


@dataclass(frozen=True)
class OCRLine:
    """One recognized text region. polygon uses image-local (x, y) coordinates."""
    text: str
    box: tuple[int, int, int, int]
    confidence: float
    polygon: tuple[tuple[int, int], ...] = ()

    @property
    def effective_polygon(self) -> tuple[tuple[int, int], ...]:
        if self.polygon:
            return self.polygon
        x1, y1, x2, y2 = self.box
        return ((x1, y1), (x2, y1), (x2, y2), (x1, y2))


@dataclass(frozen=True)
class TranslatedLine:
    text: str
    translation: str
    box: tuple[int, int, int, int]
    confidence: float
    polygon: tuple[tuple[int, int], ...] = ()
