from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def inpaint_text_regions(
    image: Image.Image, lines, *, enabled: bool = True, radius: int = 3
) -> Image.Image:
    """Inpaint a copy of image using OCR polygons; coordinates are image-local."""
    base = image.convert("RGB").copy()
    if not enabled or not lines:
        return base
    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("Inpainting cần OpenCV: pip install opencv-python") from exc

    mask = np.zeros((base.height, base.width), dtype=np.uint8)
    points = []
    for line in lines:
        polygon = getattr(line, "polygon", ()) or (
            (line.box[0], line.box[1]), (line.box[2], line.box[1]),
            (line.box[2], line.box[3]), (line.box[0], line.box[3])
        )
        points.append(np.asarray(polygon, dtype=np.int32))
    if points:
        cv2.fillPoly(mask, points, 255)
        mask = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=1)
    rgb = np.asarray(base)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    cleaned = cv2.inpaint(bgr, mask, float(radius), cv2.INPAINT_TELEA)
    return Image.fromarray(cv2.cvtColor(cleaned, cv2.COLOR_BGR2RGB))


def _font(size: int, font_path: str | None = None):
    candidates = [font_path, "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                  "/usr/share/fonts/TTF/DejaVuSans.ttf"]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            try:
                return ImageFont.truetype(candidate, size=size)
            except OSError:
                pass
    return ImageFont.load_default()


def _wrap(draw, text: str, font, max_width: int):
    words = text.split()
    if not words:
        return [text]
    lines, current = [], words[0]
    for word in words[1:]:
        candidate = current + " " + word
        if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    # Split a single overlong token character-by-character rather than drawing outside the box.
    if draw.textbbox((0, 0), current, font=font)[2] > max_width:
        chunks, chunk = [], ""
        for char in current:
            candidate = chunk + char
            if chunk and draw.textbbox((0, 0), candidate, font=font)[2] > max_width:
                chunks.append(chunk)
                chunk = char
            else:
                chunk = candidate
        if chunk:
            chunks.append(chunk)
        lines.extend(chunks)
    else:
        lines.append(current)
    return lines


def render_translations(
    image: Image.Image, lines, *, font_path: str | None = None,
    min_font_size: int = 9, max_font_size: int = 24,
    text_color=(20, 20, 20), background=(255, 255, 255, 220),
) -> Image.Image:
    """Render translated strings into OCR rectangles, shrinking font to fit."""
    result = image.convert("RGBA").copy()
    draw = ImageDraw.Draw(result)
    for item in lines:
        x1, y1, x2, y2 = item.box
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(result.width, x2), min(result.height, y2)
        width, height = x2 - x1, y2 - y1
        if width <= 2 or height <= 2:
            continue
        chosen, wrapped = _font(min_font_size, font_path), [item.translation]
        for size in range(max_font_size, min_font_size - 1, -1):
            font = _font(size, font_path)
            candidate = _wrap(draw, item.translation, font, max(1, width - 8))
            line_h = max(draw.textbbox((0, 0), "Ag", font=font)[3], size)
            if len(candidate) * line_h <= height - 4:
                chosen, wrapped = font, candidate
                break
        draw.rounded_rectangle((x1, y1, x2, y2), radius=4, fill=background)
        line_h = max(draw.textbbox((0, 0), "Ag", font=chosen)[3], min_font_size)
        total_h = len(wrapped) * line_h
        y = y1 + max(2, (height - total_h) // 2)
        for text in wrapped:
            draw.text((x1 + 4, y), text, font=chosen, fill=text_color)
            y += line_h
    return result.convert("RGB")


def process_translated_image(image: Image.Image, lines, *, remove_original=True,
                             font_path=None) -> Image.Image:
    base = inpaint_text_regions(image, lines, enabled=remove_original)
    return render_translations(base, lines, font_path=font_path)
