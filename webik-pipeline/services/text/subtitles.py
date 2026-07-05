"""
services/text/subtitles.py
Рендер subtitle PNG через Pillow.

Стиль: NetCore/Webik bold sans-serif, белый с чёрной обводкой, по центру внизу
(78% от высоты frame). Прозрачный фон (RGBA).

Что не делает (позже):
- Typing animation (буква-за-буквой) — для этого рендерим .mp4 sequence
- Word-level highlight (текущее слово ярче остального)
- Glitch / shake / kinetic typography
- Mogrt templates с встроенной анимацией
"""
from pathlib import Path
from typing import List, Optional

from PIL import Image, ImageDraw, ImageFont

from core.logger import setup_logger

log = setup_logger("subtitles")

# Default font: Bahnschrift (Windows native, чистый condensed sans-serif)
DEFAULT_FONT_PATHS = [
    r"C:\Windows\Fonts\bahnschrift.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\impact.ttf",
]

DEFAULT_FONT_SIZE = 84
DEFAULT_STROKE_WIDTH = 5
DEFAULT_TEXT_COLOR = (255, 255, 255, 255)
DEFAULT_STROKE_COLOR = (0, 0, 0, 255)
# Доля ширины frame под текст (с padding)
TEXT_MAX_WIDTH_RATIO = 0.82
# Вертикальное положение (доля высоты frame для bottom края текста)
TEXT_Y_RATIO = 0.82
LINE_SPACING_PX = 12


def _resolve_font(font_path: Optional[Path], size: int) -> ImageFont.FreeTypeFont:
    candidates = [font_path] if font_path else []
    candidates.extend(DEFAULT_FONT_PATHS)
    for fp in candidates:
        if not fp:
            continue
        try:
            return ImageFont.truetype(str(fp), size)
        except Exception:
            continue
    log.warning("Не нашёл подходящий font, использую PIL default")
    return ImageFont.load_default()


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width_px: int) -> List[str]:
    """Простой word-wrap по pixel width."""
    if not text:
        return []
    words = text.split()
    lines: List[str] = []
    current = ""
    dummy = Image.new("RGBA", (1, 1))
    draw = ImageDraw.Draw(dummy)
    for w in words:
        candidate = (current + " " + w).strip()
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] - bbox[0] <= max_width_px or not current:
            current = candidate
        else:
            lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines


def render_subtitle(
    text: str,
    out_path: Path,
    frame_w: int = 1920,
    frame_h: int = 1080,
    font_size: int = DEFAULT_FONT_SIZE,
    font_path: Optional[Path] = None,
) -> Path:
    """Рендерит PNG с прозрачным фоном и bold-текстом по центру внизу.

    Returns путь к сохранённому PNG.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGBA", (frame_w, frame_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font = _resolve_font(font_path, font_size)
    max_w_px = int(frame_w * TEXT_MAX_WIDTH_RATIO)
    lines = _wrap_text(text.upper(), font, max_w_px)
    if not lines:
        img.save(out_path, "PNG")
        return out_path

    # Высота блока
    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_heights.append(bbox[3] - bbox[1])
    block_h = sum(line_heights) + LINE_SPACING_PX * max(0, len(lines) - 1)

    # Вертикальное положение: bottom edge на TEXT_Y_RATIO * frame_h
    bottom_y = int(frame_h * TEXT_Y_RATIO)
    cursor_y = bottom_y - block_h

    for line, lh in zip(lines, line_heights):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        x = (frame_w - line_w) // 2
        # Текст с обводкой (PIL поддерживает stroke_width напрямую)
        draw.text(
            (x, cursor_y),
            line,
            font=font,
            fill=DEFAULT_TEXT_COLOR,
            stroke_width=DEFAULT_STROKE_WIDTH,
            stroke_fill=DEFAULT_STROKE_COLOR,
        )
        cursor_y += lh + LINE_SPACING_PX

    img.save(out_path, "PNG")
    return out_path
