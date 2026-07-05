"""
services/visual/vignette.py
Генерирует statiс vignette PNG (прозрачный центр → тёмные края).

Используется на V7 поверх всего, blend Multiply, для cinematic look без
полноценного Lumetri/LUT.
"""
from pathlib import Path

import numpy as np
from PIL import Image

from core.logger import setup_logger

log = setup_logger("vignette")


def generate_vignette_png(
    out_path: Path,
    frame_w: int = 1920,
    frame_h: int = 1080,
    intensity: float = 0.35,   # 2026-05-12 снижено с 0.55 — слишком тёмно по краям
    softness: float = 0.7,     # 2026-05-12 — более плавный градиент
) -> Path:
    """Генерирует RGBA vignette: прозрачный центр, чёрные края.

    intensity 0..1 — насколько тёмно по углам (0.55 = ~45% darkness в углах).
    softness 0.5..1 — гладкость градиента.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cx, cy = frame_w / 2.0, frame_h / 2.0
    max_r = float(np.hypot(cx, cy))

    yy, xx = np.indices((frame_h, frame_w), dtype=np.float32)
    dx = (xx - cx) / max_r
    dy = (yy - cy) / max_r
    r = np.sqrt(dx * dx + dy * dy)  # 0 в центре, 1 в углах

    # smooth ramp: 0..1 от softness*r → r=1
    alpha = np.clip((r - (1.0 - softness)) / softness, 0.0, 1.0)
    alpha = alpha ** 1.5  # quicker fall-off в углах
    alpha = (alpha * intensity * 255.0).astype(np.uint8)

    rgba = np.zeros((frame_h, frame_w, 4), dtype=np.uint8)
    rgba[..., 3] = alpha  # RGB остаются 0 (чёрный)

    Image.fromarray(rgba, "RGBA").save(out_path, "PNG")
    log.info(f"vignette PNG: {out_path.name} ({frame_w}x{frame_h}, intensity={intensity})")
    return out_path
