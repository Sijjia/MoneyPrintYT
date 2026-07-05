"""
services/text/level_card.py
Iceberg level title cards — большие cinematic-плашки на смене уровня.

Стиль:
- Огромная цифра уровня по центру (Impact 360px)
- Сверху мелким жирным «УРОВЕНЬ»
- Снизу subtitle (название уровня) средним размером
- Animation: fade-in 0.4s + scale-in 1.05→1.0, hold 3.0s, fade-out 0.5s
- ProRes 4444 .mov с alpha-каналом

Output: .mov с alpha (yuva444p10le), 30fps.
"""
from pathlib import Path
from typing import List, Optional, Tuple

import ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from core.logger import setup_logger

log = setup_logger("level_card")

DEFAULT_FONT_PATHS = [
    r"C:\Windows\Fonts\impact.ttf",
    r"C:\Windows\Fonts\bahnschrift.ttf",
    r"C:\Windows\Fonts\seguibl.ttf",
    r"C:\Windows\Fonts\ariblk.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
]

# Animation — карточка живёт ровно в драматической паузе voiceover (~1.5-2.5s)
FPS = 30
FADE_IN_SEC = 0.35
HOLD_SEC = 1.55
FADE_OUT_SEC = 0.55
SCALE_IN_FROM = 1.06

# Layout
NUMBER_FONT_SIZE = 360
LABEL_FONT_SIZE = 56
SUBTITLE_FONT_SIZE = 84
TEXT_COLOR = (255, 255, 255, 255)
LABEL_COLOR = (255, 80, 80, 255)   # accent red, как у PERSON-карточки
LABEL_GAP_PX = 8
SUBTITLE_GAP_PX = 80   # Impact 360px имеет крупный descent — gap нужен большой

# Дефолтные подзаголовки уровней (если topic-title не задан)
LEVEL_SUBTITLES = {
    1: "ПОВЕРХНОСТЬ",
    2: "ГЛУБЖЕ",
    3: "ТЁМНЫЕ ВОДЫ",
    4: "БЕЗДНА",
    5: "ДНО",
}


def _resolve_font(paths: List[str], size: int) -> ImageFont.FreeTypeFont:
    for fp in paths:
        try:
            return ImageFont.truetype(fp, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _draw_centered(td: ImageDraw.ImageDraw, text: str, font, fill, frame_w: int, y: int) -> Tuple[int, int]:
    """Рисует text по центру по горизонтали, верхний край = y. Возвращает (h, bbox_y_offset)."""
    bbox = td.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = (frame_w - w) // 2 - bbox[0]
    draw_y = y - bbox[1]
    td.text((x, draw_y), text, font=font, fill=fill)
    return h, bbox[1]


def _render_frame(
    frame_w: int,
    frame_h: int,
    label: str,
    number: str,
    subtitle: str,
    label_font,
    number_font,
    subtitle_font,
    overall_alpha: float,
    scale: float,
) -> Image.Image:
    """Рисует один кадр. Применяет общий alpha и scale (с центром = центр frame)."""
    img = Image.new("RGBA", (frame_w, frame_h), (0, 0, 0, 0))
    if overall_alpha <= 0.01:
        return img

    # Сначала рендерим в большом canvas и потом scale-resize, для качества scale-эффекта
    layer = Image.new("RGBA", (frame_w, frame_h), (0, 0, 0, 0))
    td = ImageDraw.Draw(layer)

    # Геометрия: всё центрируется по центру frame, по вертикали — слегка выше середины
    cy = int(frame_h * 0.46)
    # Высоты блоков
    label_bbox = td.textbbox((0, 0), label, font=label_font)
    number_bbox = td.textbbox((0, 0), number, font=number_font)
    sub_bbox = td.textbbox((0, 0), subtitle, font=subtitle_font)

    label_h = label_bbox[3] - label_bbox[1]
    number_h = number_bbox[3] - number_bbox[1]
    sub_h = sub_bbox[3] - sub_bbox[1]

    total_h = label_h + LABEL_GAP_PX + number_h + SUBTITLE_GAP_PX + sub_h
    top = cy - total_h // 2

    _draw_centered(td, label, label_font, LABEL_COLOR, frame_w, top)
    _draw_centered(td, number, number_font, TEXT_COLOR, frame_w, top + label_h + LABEL_GAP_PX)
    _draw_centered(
        td, subtitle, subtitle_font, TEXT_COLOR, frame_w,
        top + label_h + LABEL_GAP_PX + number_h + SUBTITLE_GAP_PX,
    )

    # Apply scale (resize-around-center)
    if abs(scale - 1.0) > 0.001:
        new_w = max(1, int(frame_w * scale))
        new_h = max(1, int(frame_h * scale))
        scaled = layer.resize((new_w, new_h), Image.LANCZOS)
        # crop центральный кусок frame_w × frame_h
        ox = (new_w - frame_w) // 2
        oy = (new_h - frame_h) // 2
        layer = scaled.crop((ox, oy, ox + frame_w, oy + frame_h))

    # Apply overall alpha
    if overall_alpha < 1.0:
        a = layer.split()[3]
        a = a.point(lambda p: int(p * overall_alpha))
        layer.putalpha(a)

    img.alpha_composite(layer)
    return img


def render_level_card(
    level: int,
    out_path: Path,
    subtitle_override: Optional[str] = None,
    frame_w: int = 1920,
    frame_h: int = 1080,
    hold_sec: Optional[float] = None,
) -> Tuple[Path, float]:
    """Рендерит ProRes 4444 .mov с заставкой уровня.

    Args:
        hold_sec: длительность статичного hold между fade-in и fade-out.
            Если None — берётся модульный HOLD_SEC. Используй чтобы карта
            заполнила реальный gap между сценами (а не оставляла чёрные хвосты).

    Returns (out_path, total_duration_sec).
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)

    label = "УРОВЕНЬ"
    number = str(level)
    subtitle = (subtitle_override or LEVEL_SUBTITLES.get(level, "")).upper()

    label_font = _resolve_font(DEFAULT_FONT_PATHS, LABEL_FONT_SIZE)
    number_font = _resolve_font(DEFAULT_FONT_PATHS, NUMBER_FONT_SIZE)
    subtitle_font = _resolve_font(DEFAULT_FONT_PATHS, SUBTITLE_FONT_SIZE)

    actual_hold = HOLD_SEC if hold_sec is None else max(0.05, float(hold_sec))
    total_dur = FADE_IN_SEC + actual_hold + FADE_OUT_SEC
    total_frames = int(round(total_dur * FPS))

    log.info(
        f"  level card '{label} {number} {subtitle}': "
        f"total={total_dur:.2f}s, frames={total_frames}"
    )
    process = (
        ffmpeg
        .input("pipe:", format="rawvideo", pix_fmt="rgba", s=f"{frame_w}x{frame_h}", r=FPS)
        .output(
            str(out_path),
            vcodec="prores_ks", pix_fmt="yuva444p10le",
            **{"profile:v": "4"},
        )
        .overwrite_output()
        .global_args("-loglevel", "error")
        .run_async(pipe_stdin=True, pipe_stderr=True)
    )

    try:
        for f_idx in range(total_frames):
            t = f_idx / FPS
            if t < FADE_IN_SEC:
                # Fade-in + scale-in
                p = t / FADE_IN_SEC
                alpha = p
                scale = SCALE_IN_FROM + (1.0 - SCALE_IN_FROM) * p
            elif t < FADE_IN_SEC + actual_hold:
                alpha = 1.0
                scale = 1.0
            else:
                p = (t - FADE_IN_SEC - actual_hold) / max(0.001, FADE_OUT_SEC)
                alpha = max(0.0, 1.0 - p)
                scale = 1.0 + 0.02 * p  # лёгкий push-out

            frame = _render_frame(
                frame_w, frame_h,
                label, number, subtitle,
                label_font, number_font, subtitle_font,
                overall_alpha=alpha, scale=scale,
            )
            process.stdin.write(np.array(frame).tobytes())
        process.stdin.close()
        process.wait()
    except Exception as e:
        try:
            process.stdin.close()
        except Exception:
            pass
        try:
            process.kill()
        except Exception:
            pass
        raise RuntimeError(f"ffmpeg level-card render failed: {e}") from e

    return out_path, total_dur
