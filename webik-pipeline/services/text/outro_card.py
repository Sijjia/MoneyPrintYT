"""
services/text/outro_card.py
Богатая outro CTA-карта Webik — subscribe-кнопка + slide-in анимация + частицы.

Композиция (1920x1080):
- Top: channel name large white (slides down с fade-in)
- Center: red rounded-rect SUBSCRIBE button с белым «ПОДПИШИСЬ» внутри (scale-in
  bounce + slow pulse)
- Below button: animated arrow ↓ (мягко плавающая по Y)
- Bottom: @handle smaller dim-white (slides up с fade-in)
- Background: затемнённый радиальный gradient (контент-фон виден на ~30%, но
  читаемость CTA выше)
- Particles: ~30 светящихся точек мерцают вокруг кнопки на сцене

Анимация фаз:
- 0.0-0.5s: fade-in + slide-in для всех элементов
- 0.5-4.8s: hold с пульсом subscribe + плавающей arrow + мерцающими частицами
- 4.8-5.3s: fade-out

ProRes 4444 .mov с alpha.
"""
import math
import random
from pathlib import Path
from typing import List, Tuple

import ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from core.logger import setup_logger

log = setup_logger("outro_card")

DEFAULT_FONT_PATHS = [
    r"C:\Windows\Fonts\impact.ttf",
    r"C:\Windows\Fonts\bahnschrift.ttf",
    r"C:\Windows\Fonts\seguibl.ttf",
    r"C:\Windows\Fonts\ariblk.ttf",
]

FPS = 30
FADE_IN_SEC = 0.55
HOLD_SEC = 4.4
FADE_OUT_SEC = 0.55

CHANNEL_FONT_SIZE = 110
CTA_FONT_SIZE = 140
HANDLE_FONT_SIZE = 64

BTN_BG_COLOR = (255, 70, 70)             # YouTube-red subscribe button
BTN_TEXT_COLOR = (255, 255, 255)
WHITE = (255, 255, 255)
DIM_WHITE = (200, 205, 215)
PARTICLE_COLOR = (255, 240, 200)         # тёплый sparkle


def _resolve_font(size: int) -> ImageFont.FreeTypeFont:
    for fp in DEFAULT_FONT_PATHS:
        try:
            return ImageFont.truetype(fp, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _ease_out_back(p: float) -> float:
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (p - 1) ** 3 + c1 * (p - 1) ** 2


def _draw_rounded_rect(d: ImageDraw.ImageDraw, xy, radius: int, fill: tuple) -> None:
    x0, y0, x1, y1 = xy
    d.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill)


def _generate_particle_positions(n: int, cx: int, cy: int, rx: int, ry: int, seed: int = 42) -> List[Tuple[int, int, float]]:
    """Псевдо-случайные позиции вокруг (cx, cy) в эллипсе (rx, ry).
    Возвращает [(x, y, phase)] — phase используется для мерцания."""
    rng = random.Random(seed)
    pts = []
    for _ in range(n):
        angle = rng.uniform(0, math.tau)
        # bias: концентрация ближе к краю эллипса
        r = math.sqrt(rng.uniform(0.5, 1.0))
        x = int(cx + r * rx * math.cos(angle))
        y = int(cy + r * ry * math.sin(angle))
        phase = rng.uniform(0, math.tau)
        pts.append((x, y, phase))
    return pts


def _draw_radial_bg(img: Image.Image, alpha_scalar: float) -> None:
    """Тёмный круговой gradient — затемняет края, центр на ~30% прозрачный."""
    w, h = img.size
    yy, xx = np.indices((h, w), dtype=np.float32)
    cx, cy = w / 2, h / 2
    max_r = float(np.hypot(cx, cy))
    r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / max_r
    # alpha от 120 (центр) до 220 (углы)
    alpha = (120 + 100 * np.clip(r, 0, 1)).astype(np.uint8)
    alpha = (alpha.astype(np.float32) * alpha_scalar).clip(0, 255).astype(np.uint8)
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[..., 0] = 10  # dark blue-black
    rgba[..., 1] = 14
    rgba[..., 2] = 22
    rgba[..., 3] = alpha
    bg = Image.fromarray(rgba, "RGBA")
    img.alpha_composite(bg)


def _render_frame(
    frame_w: int, frame_h: int,
    channel_name: str, channel_handle: str, cta_text: str,
    t: float, total_dur: float, intro_p: float, fade_alpha: float,
    channel_font: ImageFont.FreeTypeFont,
    cta_font: ImageFont.FreeTypeFont,
    handle_font: ImageFont.FreeTypeFont,
    particles: List[Tuple[int, int, float]],
) -> Image.Image:
    img = Image.new("RGBA", (frame_w, frame_h), (0, 0, 0, 0))
    if fade_alpha <= 0.01:
        return img

    _draw_radial_bg(img, alpha_scalar=fade_alpha)

    d = ImageDraw.Draw(img)

    # ── Channel name (top) ──
    # Slide-in сверху: y_offset(0) = -80, y_offset(1) = 0
    ch_slide = (1.0 - _ease_out_back(intro_p)) * 80
    ch_bbox = d.textbbox((0, 0), channel_name, font=channel_font)
    ch_w = ch_bbox[2] - ch_bbox[0]
    ch_x = (frame_w - ch_w) // 2 - ch_bbox[0]
    ch_y = int(frame_h * 0.18) - int(ch_slide)
    ch_a = int(255 * intro_p * fade_alpha)
    d.text((ch_x, ch_y), channel_name, font=channel_font,
           fill=(WHITE[0], WHITE[1], WHITE[2], ch_a))

    # ── Subscribe button (center) ──
    # Bounce-in scale: 0 → 1.06 → 1.0 by intro_p; затем slow pulse
    if intro_p < 1.0:
        btn_scale = _ease_out_back(intro_p)
    else:
        btn_scale = 1.0 + 0.025 * math.sin((t - FADE_IN_SEC) * math.tau * 1.0)

    btn_cx = frame_w // 2
    btn_cy = int(frame_h * 0.50)

    # Text metrics для CTA — нужно знать чтобы spec'нуть размер кнопки
    cta_bbox = d.textbbox((0, 0), cta_text, font=cta_font)
    cta_w = cta_bbox[2] - cta_bbox[0]
    cta_h = cta_bbox[3] - cta_bbox[1]

    btn_padding_x = 80
    btn_padding_y = 36
    base_btn_w = cta_w + btn_padding_x * 2
    base_btn_h = cta_h + btn_padding_y * 2

    btn_w = int(base_btn_w * btn_scale)
    btn_h = int(base_btn_h * btn_scale)
    btn_x0 = btn_cx - btn_w // 2
    btn_y0 = btn_cy - btn_h // 2
    btn_x1 = btn_x0 + btn_w
    btn_y1 = btn_y0 + btn_h
    radius = max(8, btn_h // 4)

    # Glow halo за кнопкой (rounded rect шире, мягкий красный с малым alpha)
    glow_pad = int(28 * btn_scale)
    glow_alpha = int(110 * fade_alpha * (0.7 + 0.3 * math.sin(t * math.tau * 0.7)))
    _draw_rounded_rect(
        d,
        (btn_x0 - glow_pad, btn_y0 - glow_pad, btn_x1 + glow_pad, btn_y1 + glow_pad),
        radius=radius + glow_pad,
        fill=(BTN_BG_COLOR[0], BTN_BG_COLOR[1], BTN_BG_COLOR[2], glow_alpha),
    )

    # Кнопка
    btn_a = int(255 * fade_alpha)
    _draw_rounded_rect(
        d, (btn_x0, btn_y0, btn_x1, btn_y1), radius=radius,
        fill=(BTN_BG_COLOR[0], BTN_BG_COLOR[1], BTN_BG_COLOR[2], btn_a),
    )

    # Text внутри кнопки — scaled font under bounce
    cta_font_scaled = _resolve_font(int(CTA_FONT_SIZE * btn_scale))
    cta_bbox_s = d.textbbox((0, 0), cta_text, font=cta_font_scaled)
    cw = cta_bbox_s[2] - cta_bbox_s[0]
    ch = cta_bbox_s[3] - cta_bbox_s[1]
    cx_text = btn_cx - cw // 2 - cta_bbox_s[0]
    cy_text = btn_cy - (cta_bbox_s[1] + cta_bbox_s[3]) // 2
    d.text((cx_text, cy_text), cta_text, font=cta_font_scaled,
           fill=(BTN_TEXT_COLOR[0], BTN_TEXT_COLOR[1], BTN_TEXT_COLOR[2], btn_a))

    # ── Animated arrow ↓ под кнопкой ──
    arrow_y = btn_y1 + 60
    arrow_offset = int(10 * math.sin(t * math.tau * 1.3))
    arrow_a = int(220 * fade_alpha * intro_p)
    tri = [
        (btn_cx - 28, arrow_y + arrow_offset),
        (btn_cx + 28, arrow_y + arrow_offset),
        (btn_cx, arrow_y + 38 + arrow_offset),
    ]
    d.polygon(tri, fill=(WHITE[0], WHITE[1], WHITE[2], arrow_a))

    # ── Handle (bottom) ──
    h_slide = (1.0 - _ease_out_back(intro_p)) * 60
    h_bbox = d.textbbox((0, 0), channel_handle, font=handle_font)
    h_w = h_bbox[2] - h_bbox[0]
    h_x = (frame_w - h_w) // 2 - h_bbox[0]
    h_y = int(frame_h * 0.82) + int(h_slide)
    h_a = int(220 * intro_p * fade_alpha)
    d.text((h_x, h_y), channel_handle, font=handle_font,
           fill=(DIM_WHITE[0], DIM_WHITE[1], DIM_WHITE[2], h_a))

    # ── Particles мерцающие вокруг кнопки ──
    for (px, py, phase) in particles:
        twinkle = 0.5 + 0.5 * math.sin(t * math.tau * 0.8 + phase)
        sz = 3 + int(3 * twinkle)
        p_a = int(180 * twinkle * fade_alpha * intro_p)
        if p_a < 4:
            continue
        d.ellipse(
            [px - sz, py - sz, px + sz, py + sz],
            fill=(PARTICLE_COLOR[0], PARTICLE_COLOR[1], PARTICLE_COLOR[2], p_a),
        )

    return img


def render_outro_card(
    out_path: Path,
    channel_name: str = "WEBIK STUDIO",
    channel_handle: str = "@WebikStudio",
    cta_text: str = "ПОДПИШИСЬ",
    frame_w: int = 1920,
    frame_h: int = 1080,
) -> Tuple[Path, float]:
    """Рендерит rich outro CTA-карту как ProRes 4444 .mov с alpha."""
    out_path.parent.mkdir(parents=True, exist_ok=True)

    channel_font = _resolve_font(CHANNEL_FONT_SIZE)
    cta_font = _resolve_font(CTA_FONT_SIZE)
    handle_font = _resolve_font(HANDLE_FONT_SIZE)

    total_dur = FADE_IN_SEC + HOLD_SEC + FADE_OUT_SEC
    total_frames = int(round(total_dur * FPS))

    # Particle positions — раз на render, эллипс вокруг центра кнопки
    btn_cy_est = int(frame_h * 0.50)
    particles = _generate_particle_positions(
        n=32, cx=frame_w // 2, cy=btn_cy_est,
        rx=int(frame_w * 0.32), ry=int(frame_h * 0.20),
        seed=hash(channel_name) & 0xFFFF,
    )

    log.info(
        f"  outro card '{channel_name} / {cta_text} / {channel_handle}': "
        f"total={total_dur:.2f}s, frames={total_frames}, particles={len(particles)}"
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

    expected_bytes = frame_w * frame_h * 4
    try:
        for f_idx in range(total_frames):
            t = f_idx / FPS
            if t < FADE_IN_SEC:
                intro_p = t / FADE_IN_SEC
                fade_alpha = intro_p
            elif t < FADE_IN_SEC + HOLD_SEC:
                intro_p = 1.0
                fade_alpha = 1.0
            else:
                intro_p = 1.0
                fp = (t - FADE_IN_SEC - HOLD_SEC) / max(0.001, FADE_OUT_SEC)
                fade_alpha = max(0.0, 1.0 - fp)
            frame = _render_frame(
                frame_w, frame_h,
                channel_name, channel_handle, cta_text,
                t, total_dur, intro_p, fade_alpha,
                channel_font, cta_font, handle_font,
                particles,
            )
            buf = np.array(frame).tobytes()
            if len(buf) != expected_bytes:
                buf = b"\x00" * expected_bytes
            process.stdin.write(buf)
        process.stdin.close()
        rc = process.wait()
        if rc != 0:
            stderr = (process.stderr.read() or b"").decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"ffmpeg exit={rc} stderr={stderr}")
    except Exception as e:
        try:
            process.stdin.close()
        except Exception:
            pass
        try:
            process.kill()
        except Exception:
            pass
        raise RuntimeError(f"outro render failed: {e}") from e

    return out_path, total_dur
