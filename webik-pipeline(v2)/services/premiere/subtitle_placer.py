"""
services/premiere/subtitle_placer.py
Размещение subtitle PNG на V3 синхронно с whisper-sentences.

Каждое предложение из alignment.sentences[] →
- PNG через services.text.subtitles.render_subtitle (1920x1080 transparent)
- Сохранён в projects/<id>/assets/subtitles/sentence_<N>.png
- Импорт в Premiere → insertClip на V3 в sentence.start
- Длительность = sentence.end - sentence.start
- Fade-in 0.1s + fade-out 0.1s (через Opacity keyframes)
"""
from pathlib import Path
from typing import Dict, List, Optional

from pymiere.wrappers import time_from_seconds

from core.logger import setup_logger
from services.premiere.effects import (
    apply_dip_to_black_fade,
    find_clip_by_timeline_start,
)
from services.premiere.pymiere_wrapper import import_files
from services.text.subtitles import render_subtitle

log = setup_logger("subtitle_placer")

SUBTITLE_FADE_IN_SEC = 0.10
SUBTITLE_FADE_OUT_SEC = 0.10
# Минимальная длительность субтитра (если фраза короче — расширяем)
MIN_SUBTITLE_DUR_SEC = 0.6


def place_subtitles(
    sequence,
    sentences: List[Dict],
    project_dir: Path,
    frame_w: int = 1920,
    frame_h: int = 1080,
) -> int:
    """Расставляет subtitle PNG на V3 по whisper-sentences.

    Args:
        sentences: список из alignment["sentences"] = [{text, start, end}, ...]
        project_dir: путь к проекту (для записи PNG в assets/subtitles/)

    Returns:
        Кол-во размещённых subtitle clip'ов.
    """
    if not sentences:
        log.info("Нет whisper-sentences для субтитров")
        return 0

    subtitles_dir = project_dir / "assets" / "subtitles"
    subtitles_dir.mkdir(parents=True, exist_ok=True)

    video_tracks = sequence.videoTracks
    if video_tracks.numTracks < 3:
        log.warning(
            f"V3 нет в sequence ({video_tracks.numTracks} tracks) — субтитры не положу"
        )
        return 0
    v3 = video_tracks[2]

    # 1. Рендерим все PNG
    pngs: List[Path] = []
    for i, sent in enumerate(sentences):
        text = sent.get("text", "").strip()
        if not text:
            continue
        out = subtitles_dir / f"sentence_{i:03d}.png"
        if not out.exists():
            try:
                render_subtitle(text, out, frame_w=frame_w, frame_h=frame_h)
            except Exception as e:
                log.warning(f"  sentence {i}: render failed: {e}")
                continue
        pngs.append(out)

    if not pngs:
        log.warning("Не удалось ни одного субтитра отрендерить")
        return 0
    log.info(f"Субтитры: отрендерено {len(pngs)} PNG")

    # 2. Импортируем все PNG одним пакетом
    imported = import_files(pngs)
    items_by_name = {it.name: it for it in imported}

    placed = 0
    for i, sent in enumerate(sentences):
        text = sent.get("text", "").strip()
        if not text:
            continue
        png_path = subtitles_dir / f"sentence_{i:03d}.png"
        if not png_path.exists():
            continue
        item = items_by_name.get(png_path.name) or items_by_name.get(png_path.stem)
        if item is None:
            log.warning(f"  sentence {i}: не нашёл импортированный item")
            continue

        start = float(sent.get("start", 0.0))
        end = float(sent.get("end", start + MIN_SUBTITLE_DUR_SEC))
        if end - start < MIN_SUBTITLE_DUR_SEC:
            end = start + MIN_SUBTITLE_DUR_SEC

        try:
            v3.insertClip(item, time_from_seconds(start))
        except Exception as e:
            log.warning(f"  sentence {i}: V3.insertClip упал: {e}")
            continue

        # Trim до точной длительности
        clip = find_clip_by_timeline_start(v3, start)
        if clip is not None:
            try:
                clip.end = time_from_seconds(end)
            except Exception as e:
                log.warning(f"  sentence {i}: trim failed: {e}")
            apply_dip_to_black_fade(
                clip,
                fade_in_sec=SUBTITLE_FADE_IN_SEC,
                fade_out_sec=SUBTITLE_FADE_OUT_SEC,
                do_fade_in=True,
                do_fade_out=True,
            )

        placed += 1
        preview = text[:50] + ("..." if len(text) > 50 else "")
        log.info(f"  V3 sentence {i}: {start:.2f}s→{end:.2f}s «{preview}»")

    return placed
