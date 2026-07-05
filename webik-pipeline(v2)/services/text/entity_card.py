"""
services/text/entity_card.py
Webik-стиль entity overlay (по референсу из «Айсберги-Китай»).

Стиль:
- Только крупный белый CAPS-текст на прозрачном фоне
- Без plate, без accent-label, без shadow
- Typewriter: символ за символом, блочный курсор █ только пока печатается
- После печати — текст просто стоит (cursor OFF), потом fade-out
- ProRes 4444 .mov с alpha-каналом (Premiere играет с прозрачным фоном)

Output: .mov с alpha (yuva444p10le), 30fps.
"""
from pathlib import Path
from typing import List, Optional, Tuple

import ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from core.logger import setup_logger

log = setup_logger("entity_card")

# Шрифт — Impact / Bahnschrift Bold / Arial Black: жирный condensed sans-serif как на референсе
DEFAULT_FONT_PATHS = [
    r"C:\Windows\Fonts\impact.ttf",
    r"C:\Windows\Fonts\bahnschrift.ttf",
    r"C:\Windows\Fonts\seguibl.ttf",   # Segoe UI Black
    r"C:\Windows\Fonts\ariblk.ttf",    # Arial Black
    r"C:\Windows\Fonts\arialbd.ttf",
]

# Параметры анимации
FPS = 30
TYPING_CHARS_PER_SEC = 22.0
HOLD_AFTER_TYPING_SEC = 3.2  # карточка долго стоит — успеть прочитать
FADE_OUT_SEC = 0.45
CURSOR_BLINK_HZ = 2.5
CURSOR_CHAR = "█"

# Параметры визуала
MAIN_FONT_SIZE = 130           # крупно как на скрине
TEXT_COLOR = (255, 255, 255, 255)
TEXT_Y_RATIO = 0.78            # bottom edge text block at 78% of frame height (нижняя треть)


def _resolve_font(paths: List[str], size: int) -> ImageFont.FreeTypeFont:
    for fp in paths:
        try:
            return ImageFont.truetype(fp, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _render_frame(
    frame_w: int,
    frame_h: int,
    main_text_visible: str,
    cursor_on: bool,
    main_font: ImageFont.FreeTypeFont,
    overall_alpha: float = 1.0,
    final_text: str = "",
) -> Image.Image:
    """Render single frame. `final_text` — финальный текст; используется как
    ANCHOR для позиции (с учётом курсора), чтобы буквы не «съезжали» когда
    typewriter подставляет каждую следующую букву (per-frame recenter = jitter).
    """
    img = Image.new("RGBA", (frame_w, frame_h), (0, 0, 0, 0))
    if overall_alpha <= 0.01:
        return img

    td = ImageDraw.Draw(img)
    main_with_cursor = main_text_visible + (CURSOR_CHAR if cursor_on else "")

    # Anchor по финальному состоянию (full text + cursor), позиция стабильна
    anchor_text = (final_text or main_with_cursor) + CURSOR_CHAR
    abox = td.textbbox((0, 0), anchor_text, font=main_font)
    a_w = abox[2] - abox[0]
    bottom_y = int(frame_h * TEXT_Y_RATIO)
    x = (frame_w - a_w) // 2 - abox[0]
    y = bottom_y - abox[3]  # bottom-aligned: bbox.bottom touches bottom_y

    td.text((x, y), main_with_cursor, font=main_font, fill=TEXT_COLOR)

    if overall_alpha < 1.0:
        a = img.split()[3]
        a = a.point(lambda p: int(p * overall_alpha))
        img.putalpha(a)
    return img


def render_typewriter_card(
    entity_type: str,
    text: str,
    out_path: Path,
    photo_path: Optional[Path] = None,
    frame_w: int = 1920,
    frame_h: int = 1080,
) -> Tuple[Path, float]:
    """Рендерит ProRes 4444 .mov с typing animation на прозрачном фоне.

    Returns (out_path, total_duration_sec).
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)

    text_upper = text.upper()
    main_font = _resolve_font(DEFAULT_FONT_PATHS, MAIN_FONT_SIZE)

    # Считаем фазы
    n_chars = max(1, len(text_upper))
    typing_dur = n_chars / TYPING_CHARS_PER_SEC
    hold_dur = HOLD_AFTER_TYPING_SEC
    fade_dur = FADE_OUT_SEC
    total_dur = typing_dur + hold_dur + fade_dur
    total_frames = int(round(total_dur * FPS))

    # ffmpeg writer (ProRes 4444 with alpha)
    log.info(
        f"  render '{text}' ({entity_type}): "
        f"{n_chars} chars, total={total_dur:.2f}s, frames={total_frames}"
    )
    process = (
        ffmpeg
        .input("pipe:", format="rawvideo", pix_fmt="rgba", s=f"{frame_w}x{frame_h}", r=FPS)
        .output(
            str(out_path),
            vcodec="prores_ks",
            pix_fmt="yuva444p10le",
            **{"profile:v": "4"},
        )
        .overwrite_output()
        .global_args("-loglevel", "error", "-stats_period", "60")
        .run_async(pipe_stdin=True, pipe_stderr=True)
    )

    expected_bytes_per_frame = frame_w * frame_h * 4  # RGBA
    try:
        for f_idx in range(total_frames):
            t = f_idx / FPS

            if t < typing_dur:
                # Typing phase: символы появляются + блинкующий курсор
                chars_visible = min(n_chars, int(t * TYPING_CHARS_PER_SEC))
                main_visible = text_upper[:chars_visible]
                cursor_on = (int(t * CURSOR_BLINK_HZ * 2) % 2 == 0)
                alpha = 1.0
            elif t < typing_dur + hold_dur:
                # Hold: чистый текст без курсора (как на скрине)
                main_visible = text_upper
                cursor_on = False
                alpha = 1.0
            else:
                # Fade-out
                main_visible = text_upper
                cursor_on = False
                fade_t = (t - typing_dur - hold_dur) / max(0.001, fade_dur)
                alpha = max(0.0, 1.0 - fade_t)

            frame = _render_frame(
                frame_w, frame_h,
                main_visible, cursor_on,
                main_font,
                overall_alpha=alpha,
                final_text=text_upper,
            )
            buf = np.array(frame).tobytes()
            # Защита от mismatch: если PIL вернул неожиданный размер, ffmpeg
            # упадёт с [Errno 22]. Лучше подменить на пустой кадр чем порвать pipe.
            if len(buf) != expected_bytes_per_frame:
                log.warning(
                    f"frame {f_idx} buffer size mismatch: "
                    f"got {len(buf)} bytes, expected {expected_bytes_per_frame} "
                    f"(text='{main_visible}'). Подменяю на прозрачный кадр."
                )
                buf = b"\x00" * expected_bytes_per_frame
            process.stdin.write(buf)
        process.stdin.close()
        rc = process.wait()
        if rc != 0:
            stderr_bytes = b""
            try:
                stderr_bytes = process.stderr.read() or b""
            except Exception:
                pass
            raise RuntimeError(
                f"ffmpeg exit code={rc}; stderr={stderr_bytes.decode('utf-8', errors='replace')[:500]}"
            )
    except Exception as e:
        # Захватываем stderr ffmpeg'а — без этого диагностика [Errno 22] невозможна
        stderr_text = ""
        try:
            stderr_text = (process.stderr.read() or b"").decode("utf-8", errors="replace")[:500]
        except Exception:
            pass
        try:
            process.stdin.close()
        except Exception:
            pass
        try:
            process.kill()
        except Exception:
            pass
        msg = f"ffmpeg render failed: {e}"
        if stderr_text:
            msg += f" | ffmpeg stderr: {stderr_text}"
        raise RuntimeError(msg) from e

    return out_path, total_dur
