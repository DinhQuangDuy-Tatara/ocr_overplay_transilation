import pytest
from ocr_overlay.capture.grim import parse_slurp_region, Region


def test_parse_slurp_region():
    assert parse_slurp_region("12,34 500x300") == Region(12, 34, 500, 300)
    assert parse_slurp_region("-10,20 100x80") == Region(-10, 20, 100, 80)


@pytest.mark.parametrize("value", ["", "1,2", "1,2 0x10", "a,b 1x2"])
def test_parse_invalid_region(value):
    with pytest.raises(ValueError):
        parse_slurp_region(value)
