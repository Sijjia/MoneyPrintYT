"""
services/visual/parallax.py
Рендер 2.5D parallax-видео из image + depth-map.

Эффект: камера тонко панорамирует и плавно zoom'ит, объекты на разной глубине
двигаются с разной скоростью — статичное фото «оживает».

Алгоритм:
1. Compute depth (services.visual.depth.estimate_depth) — H×W в [0..1]
2. Camera path: ease-in-out по `t ∈ [0..1]`, lateral pan + slight zoom
3. Per-frame: cv2.remap(image, displacement_field) где displacement_field
   = depth-modulated camera offset
4. ffmpeg pipe rgb24 frames → mp4 H.264

Output: .mp4 при 30 fps, длительность как заказана. Pad-image слегка
больше frame чтобы parallax не показывал чёрные края.
"""
import math
from pathlib import Path
from typing import Optional, Tuple

import cv2
import ffmpeg
import numpy as np
from PIL import Image

from core.logger import setup_logger
from services.visual.depth import estimate_depth

log = setup_logger("parallax")

FPS = 30
# Радиус параллакса (в pixels frame-space, при depth=1.0 макс смещение)
MAX_DX_PX = 60.0
MAX_DY_PX = 18.0
# Zoom (multiplier in [start..end])
ZOOM_START = 1.04
ZOOM_END = 1.10


def _ease_in_out(t: float) -> float:
    """Smoothstep ease для красивого движения камеры."""
    return t * t * (3.0 - 2.0 * t)


def _camera_path(t: float) -> Tuple[float, float, float]:
    """Возвращает (dx_norm, dy_norm, zoom) для параметра времени t∈[0..1].

    dx_norm/dy_norm в [-1..1], zoom — абсолютный множитель.
    Используем ease-in-out для плавности и lissajous для разнообразия.
    """
    e = _ease_in_out(t)
    # Lateral pan слева-направо, лёгкая вертикаль
    dx = math.cos(math.pi * (1.0 - e)) * 0.7  # -0.7 → +0.7
    dy = math.sin(math.pi * 0.5 * e) * 0.4  # 0 → 0.4
    zoom = ZOOM_START + (ZOOM_END - ZOOM_START) * e
    return dx, dy, zoom


def _resize_cover(img: np.ndarray, frame_w: int, frame_h: int) -> np.ndarray:
    """Resize image чтобы покрыть frame целиком (cover-fit), без обрезки.

    Возвращает image НЕ меньше frame_w/frame_h по обоим осям.
    Crop-чение делается уже на этапе warp.
    """
    h, w = img.shape[:2]
    src_aspect = w / h
    tgt_aspect = frame_w / frame_h
    # Scale так чтобы покрыть frame с запасом по обеим осям (для parallax pan)
    # Используем pad-multiplier — даём 15% запаса чтобы pan не вылез за край
    pad = 1.15
    if src_aspect > tgt_aspect:
        new_h = int(frame_h * pad)
        new_w = int(new_h * src_aspect)
    else:
        new_w = int(frame_w * pad)
        new_h = int(new_w / src_aspect)
    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA if w > new_w else cv2.INTER_LANCZOS4)


def render_parallax_video(
    image_path: Path,
    out_path: Path,
    duration_sec: float,
    frame_w: int = 1920,
    frame_h: int = 1080,
    depth_map: Optional[np.ndarray] = None,
) -> bool:
    """Рендерит parallax mp4 из image+depth.

    Args:
        image_path: исходное фото
        out_path: куда писать .mp4
        duration_sec: длительность ролика
        depth_map: предвычисленная depth (H×W [0..1]). Если None — посчитаем здесь.

    Returns True если успех.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not image_path.exists():
        log.warning(f"image not found: {image_path}")
        return False

    img_pil = Image.open(image_path).convert("RGB")
    img = np.asarray(img_pil)  # H×W×3, uint8

    if depth_map is None:
        depth_map = estimate_depth(image_path)
    if depth_map is None:
        log.warning(f"  depth не получен для {image_path.name}, пропускаю parallax")
        return False

    # Resize image+depth до общего размера (cover frame с запасом)
    cover = _resize_cover(img, frame_w, frame_h)
    cover_h, cover_w = cover.shape[:2]
    depth_resized = cv2.resize(depth_map, (cover_w, cover_h), interpolation=cv2.INTER_LINEAR)

    # Pre-build base meshgrid (constant)
    xx, yy = np.meshgrid(np.arange(cover_w, dtype=np.float32), np.arange(cover_h, dtype=np.float32))

    # Center crop coords (статичный без depth = просто центральный кроп)
    crop_cx, crop_cy = cover_w / 2.0, cover_h / 2.0
    half_w, half_h = frame_w / 2.0, frame_h / 2.0

    total_frames = int(round(duration_sec * FPS))
    log.info(
        f"  parallax '{image_path.name}': {duration_sec:.2f}s × {FPS}fps "
        f"= {total_frames} frames, cover={cover_w}×{cover_h}"
    )

    process = (
        ffmpeg
        .input("pipe:", format="rawvideo", pix_fmt="rgb24", s=f"{frame_w}x{frame_h}", r=FPS)
        .output(
            str(out_path),
            vcodec="libx264", pix_fmt="yuv420p",
            preset="veryfast", crf=18,
            **{"movflags": "+faststart"},
        )
        .overwrite_output()
        .global_args("-loglevel", "error")
        .run_async(pipe_stdin=True, pipe_stderr=True)
    )

    try:
        for f_idx in range(total_frames):
            t = f_idx / max(1, total_frames - 1)
            dx_n, dy_n, zoom = _camera_path(t)

            # Camera offset in pixels (frame-space)
            cam_dx = dx_n * MAX_DX_PX
            cam_dy = dy_n * MAX_DY_PX

            # Per-pixel displacement: ближние пиксели сдвигаются больше
            # dispersion = (depth - 0.5) * 2 ∈ [-1..1]
            d = (depth_resized * 2.0 - 1.0)  # центрированно вокруг 0
            disp_x = cam_dx * d  # H×W
            disp_y = cam_dy * d

            # Sample coords в cover-space:
            # Для каждого output pixel (u, v) в frame [0..frame_w/h] —
            # читаем cover в (cx + (u - half_w) / zoom + disp_x, cy + ...)
            uu, vv = np.meshgrid(
                np.arange(frame_w, dtype=np.float32),
                np.arange(frame_h, dtype=np.float32),
            )
            base_x = crop_cx + (uu - half_w) / zoom
            base_y = crop_cy + (vv - half_h) / zoom

            # Нужно interpolate displacement по base_x/base_y → текущая cover-grid не bbox
            # Для простоты: возьмём depth в центральной точке (clamp)
            ix = np.clip(base_x.astype(np.int32), 0, cover_w - 1)
            iy = np.clip(base_y.astype(np.int32), 0, cover_h - 1)
            sample_dx = disp_x[iy, ix]
            sample_dy = disp_y[iy, ix]

            map_x = (base_x + sample_dx).astype(np.float32)
            map_y = (base_y + sample_dy).astype(np.float32)

            warped = cv2.remap(
                cover, map_x, map_y,
                interpolation=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_REFLECT_101,
            )

            process.stdin.write(warped.tobytes())

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
        log.warning(f"  parallax render failed: {e}")
        return False

    log.info(f"  parallax готов: {out_path.name}")
    return True
