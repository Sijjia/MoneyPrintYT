"""Рендерит один статичный кадр карточки в PNG для визуального сравнения со скрином."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.text.entity_card import (
    DEFAULT_FONT_PATHS, MAIN_FONT_SIZE, _render_frame, _resolve_font,
)
from PIL import Image

font = _resolve_font(DEFAULT_FONT_PATHS, MAIN_FONT_SIZE)
img = _render_frame(
    frame_w=1920,
    frame_h=1080,
    main_text_visible="1962 ГОД",
    cursor_on=False,  # как на скрине, текст уже напечатан
    main_font=font,
    overall_alpha=1.0,
)

# Подложим красный фон чтобы было похоже на скрин
bg = Image.new("RGB", (1920, 1080), (190, 30, 30))
bg.paste(img, (0, 0), img)
out = Path(__file__).parent / "preview_card.png"
bg.save(out)
print(f"Saved: {out}")
