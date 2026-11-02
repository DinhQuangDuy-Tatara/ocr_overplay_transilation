from PIL import Image
from ocr_overlay.ocr.paddle_adapter import PaddleOCRAdapter


def test_parse_legacy_result_preserves_polygon_and_box():
    raw = [[
        ([[1.2, 2.1], [9.8, 2.0], [10.0, 8.9], [1.0, 9.0]], ("안녕", 0.97))
    ]]
    lines = PaddleOCRAdapter._parse_legacy(raw)
    assert len(lines) == 1
    assert lines[0].text == "안녕"
    assert lines[0].box == (1, 2, 10, 9)
    assert lines[0].confidence == 0.97
    assert len(lines[0].polygon) == 4


def test_recognize_rejects_non_pil_input():
    import pytest
    with pytest.raises(TypeError):
        PaddleOCRAdapter().recognize("not an image", "ko")
