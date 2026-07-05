"""Превью одного level card в PNG (статичный кадр) + .mov full anim."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image

from services.text.level_card import (
    DEFAULT_FONT_PATHS, LABEL_FONT_SIZE, NUMBER_FONT_SIZE, SUBTITLE_FONT_SIZE,
    _render_frame, _resolve_font, render_level_card,
)

# 1. Static preview (один кадр)
label_font = _resolve_font(DEFAULT_FONT_PATHS, LABEL_FONT_SIZE)
number_font = _resolve_font(DEFAULT_FONT_PATHS, NUMBER_FONT_SIZE)
subtitle_font = _resolve_font(DEFAULT_FONT_PATHS, SUBTITLE_FONT_SIZE)

img = _render_frame(
    frame_w=1920, frame_h=1080,
    label="УРОВЕНЬ", number="1", subtitle="ПОВЕРХНОСТЬ",
    label_font=label_font, number_font=number_font, subtitle_font=subtitle_font,
    overall_alpha=1.0, scale=1.0,
)
bg = Image.new("RGB", (1920, 1080), (15, 15, 18))
bg.paste(img, (0, 0), img)
out_png = Path(__file__).parent / "preview_level_card.png"
bg.save(out_png)
print(f"PNG preview: {out_png}")

# 2. Full .mov render
out_mov = Path(__file__).parent / "preview_level_card.mov"
t0 = time.time()
render_level_card(level=1, out_path=out_mov)
print(f"MOV: {out_mov} ({out_mov.stat().st_size / 1024:.0f} KB, {time.time() - t0:.1f}s)")
