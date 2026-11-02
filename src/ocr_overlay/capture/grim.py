import re
import shutil
import subprocess
from dataclasses import dataclass
from io import BytesIO
from PIL import Image


@dataclass(frozen=True)
class Region:
    x: int
    y: int
    width: int
    height: int


_REGION = re.compile(r"^\s*(-?\d+),(-?\d+)\s+(\d+)x(\d+)\s*$")


def parse_slurp_region(value: str) -> Region:
    match = _REGION.match(value)
    if not match:
        raise ValueError(f"Không đọc được tọa độ slurp: {value!r}")
    x, y, width, height = map(int, match.groups())
    if width <= 0 or height <= 0:
        raise ValueError("Vùng chọn phải có chiều rộng và chiều cao dương")
    return Region(x, y, width, height)


class GrimCapture:
    """One-shot Wayland capture PoC using slurp + grim; not a streaming backend."""

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    def select_region(self) -> Region:
        if not shutil.which("slurp"):
            raise RuntimeError("Không tìm thấy slurp. Cài bằng: sudo pacman -S slurp")
        result = subprocess.run(
            ["slurp"], check=False, capture_output=True, text=True, timeout=self.timeout
        )
        if result.returncode != 0:
            raise RuntimeError("Đã hủy chọn vùng hoặc slurp gặp lỗi")
        return parse_slurp_region(result.stdout)

    def capture(self, region: Region) -> Image.Image:
        if not shutil.which("grim"):
            raise RuntimeError("Không tìm thấy grim. Cài bằng: sudo pacman -S grim")
        geometry = f"{region.x},{region.y} {region.width}x{region.height}"
        result = subprocess.run(
            ["grim", "-g", geometry, "-"], check=False,
            capture_output=True, timeout=self.timeout
        )
        if result.returncode != 0:
            message = result.stderr.decode(errors="replace")[:500]
            raise RuntimeError(f"grim capture thất bại: {message}")
        try:
            with Image.open(BytesIO(result.stdout)) as image:
                return image.convert("RGB")
        except Exception as exc:
            raise RuntimeError("grim không trả về dữ liệu ảnh hợp lệ") from exc
