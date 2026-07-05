"""
services/visual/depth.py
Depth-map estimation через Depth Anything V2 Small (HuggingFace).

Используется для parallax 3D рендера статичных фото в Stage 4.
Возвращает np.ndarray shape (H, W) values в [0..1] — где 1 = ближайший объект, 0 = фон.

Модель ~25MB, кэшируется HF в %USERPROFILE%/.cache/huggingface/.
На CPU: ~5-10 сек на image 1920x1080 (resize до 518 внутри модели).
"""
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image

from core.logger import setup_logger

log = setup_logger("depth")

_PIPE = None
_PIPE_TRIED = False
MODEL_NAME = "depth-anything/Depth-Anything-V2-Small-hf"


def _ensure_pipeline():
    """Загружает Depth Anything pipeline (lazy, singleton)."""
    global _PIPE, _PIPE_TRIED
    if _PIPE is not None or _PIPE_TRIED:
        return _PIPE
    _PIPE_TRIED = True
    try:
        from transformers import pipeline
        log.info(f"Загружаю Depth Anything модель: {MODEL_NAME}")
        _PIPE = pipeline(
            task="depth-estimation",
            model=MODEL_NAME,
            device="cpu",  # CUDA не доступна
        )
        log.info("Depth Anything готов")
        return _PIPE
    except Exception as e:
        log.warning(f"Depth Anything load failed: {e}")
        return None


def estimate_depth(image_path: Path) -> Optional[np.ndarray]:
    """Возвращает depth-map нормализованный в [0..1].

    Returns np.ndarray shape (H, W) float32, где 1 = ближний план, 0 = фон.
    Размер совпадает с image (Depth Anything resamples обратно).
    Returns None если модель не загрузилась или ошибка.
    """
    pipe = _ensure_pipeline()
    if pipe is None:
        return None
    try:
        img = Image.open(image_path).convert("RGB")
        result = pipe(img)
        # result["depth"] — PIL Image (grayscale), result["predicted_depth"] — torch tensor
        depth_pil = result["depth"]
        depth = np.asarray(depth_pil, dtype=np.float32)
        # Normalize 0..1 (Depth Anything возвращает inverse depth, ближе=ярче — нам как раз)
        d_min, d_max = float(depth.min()), float(depth.max())
        if d_max - d_min < 1e-6:
            return np.zeros_like(depth)
        depth = (depth - d_min) / (d_max - d_min)
        return depth
    except Exception as e:
        log.warning(f"depth estimation упал для {image_path.name}: {e}")
        return None
