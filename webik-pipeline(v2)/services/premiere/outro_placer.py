"""
services/premiere/outro_placer.py
Размещает финальную CTA-карту в конце таймлайна (продлевая sequence на ~5s).

Кладёт на V8 (или новый трек если V8 занят чартом во время outro — но обычно
outro в самом конце, после всех чартов). Карта рендерится через
services/text/outro_card.py с params из core/config.py.
"""
import hashlib
from pathlib import Path
from typing import Optional

from pymiere.wrappers import time_from_seconds

from core.config import get_settings
from core.logger import setup_logger
from services.premiere.pymiere_wrapper import ensure_video_tracks, import_files
from services.text.outro_card import render_outro_card

log = setup_logger("outro_placer")

# V10 = PIL outro CTA (всегда)
# V11 = опциональный AE overlay (если пользователь положил .mov в templates/outro/ae_overlay.mov)
V10_INDEX = 9
V11_INDEX = 10
LEAD_IN_SEC = 0.3  # outro начинается за 0.3s до конца контента (мягкий fade-in over content)
AE_OVERLAY_RELATIVE = Path("templates") / "outro" / "ae_overlay.mov"


def place_outro_card(
    sequence,
    project_dir: Path,
    content_end_sec: float,
    frame_w: int = 1920,
    frame_h: int = 1080,
) -> bool:
    """Кладёт outro CTA в конце таймлайна. Returns True если размещено."""
    settings = get_settings()
    channel_name = settings.channel_name
    channel_handle = settings.channel_handle
    cta_text = "ПОДПИШИСЬ"

    outro_dir = project_dir / "assets" / "outro"
    outro_dir.mkdir(parents=True, exist_ok=True)

    # Cache key по content (channel name может смениться → re-render)
    h = hashlib.md5(
        f"{channel_name}|{channel_handle}|{cta_text}|{frame_w}x{frame_h}".encode("utf-8")
    ).hexdigest()[:8]
    out_mov = outro_dir / f"outro_{h}.mov"

    if out_mov.exists() and out_mov.stat().st_size > 1000:
        log.info(f"  outro cache hit ({out_mov.name})")
    else:
        try:
            render_outro_card(
                out_mov,
                channel_name=channel_name,
                channel_handle=channel_handle,
                cta_text=cta_text,
                frame_w=frame_w, frame_h=frame_h,
            )
        except Exception as e:
            log.warning(f"  outro render failed: {e}")
            return False

    if not ensure_video_tracks(sequence, V10_INDEX + 1):
        log.warning("V10 track создать не получилось — outro пропускаю")
        return False
    v10 = sequence.videoTracks[V10_INDEX]

    imported = import_files([out_mov])
    if not imported:
        log.warning("  outro import_files вернул пусто")
        return False
    item = imported[0]

    # Стартуем за LEAD_IN_SEC до конца контента — fade-in начинает накрывать
    # последний кадр контента, smooth handoff
    start_sec = max(0.0, content_end_sec - LEAD_IN_SEC)
    try:
        v10.insertClip(item, time_from_seconds(start_sec))
    except Exception as e:
        log.warning(f"  outro V10.insertClip failed: {e}")
        return False

    log.info(f"  V10 outro '{channel_name}/{cta_text}/{channel_handle}' @{start_sec:.2f}s")

    # Опционально: AE overlay (.mov с alpha) поверх PIL CTA на V11
    _try_place_ae_overlay(sequence, start_sec, frame_w, frame_h)

    return True


def _try_place_ae_overlay(sequence, start_sec: float, frame_w: int, frame_h: int) -> bool:
    """Если в templates/outro/ae_overlay.mov лежит AE-рендер (alpha ProRes 4444) —
    кладём на V11 синхронно с PIL outro. Иначе пропускаем (no-op)."""
    # Ищем относительно рабочей директории пайплайна
    candidates = [
        Path.cwd() / AE_OVERLAY_RELATIVE,
        Path(__file__).resolve().parent.parent.parent / AE_OVERLAY_RELATIVE,
    ]
    ae_path: Optional[Path] = None
    for c in candidates:
        if c.exists() and c.stat().st_size > 1000:
            ae_path = c
            break
    if ae_path is None:
        return False

    if not ensure_video_tracks(sequence, V11_INDEX + 1):
        return False
    v11 = sequence.videoTracks[V11_INDEX]
    try:
        imported = import_files([ae_path])
        if not imported:
            return False
        v11.insertClip(imported[0], time_from_seconds(start_sec))
        log.info(f"  V11 AE overlay {ae_path.name} @{start_sec:.2f}s")
        return True
    except Exception as e:
        log.warning(f"  AE overlay placement failed: {e}")
        return False
