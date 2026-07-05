"""
services/premiere/archive_clip_placer.py
Авто-привязка архивных видео-клипов (YouTube/архив) к сценам в таймлайне.

Это «правильная» укладка вместо ручного тыка в t=0: каждый клип из manifest,
у которого source = youtube / youtube-auto и kind = video, садится НАКЛАДКОЙ
(cutaway) на верхнюю свободную дорожку РОВНО на тайм-окно своей сцены —
момент, когда озвучка про этот факт. Под клипом продолжает идти основное
видео (V3) и голос (A1) — как настоящий монтаж B-roll.

Тайминги сцен берём из alignment["scenes"][sid] = {start, end, ...}.
Клип тримим до min(своя длина, окно сцены, max_clip_sec), мьютим, добавляем
короткие opacity-fade на входе/выходе.

Связка: Stage 4 (_build_media_manifest, тир auto-archive) кладёт клипы и
прописывает их в manifest → этот модуль расставляет их по слотам сцен.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from pymiere.wrappers import time_from_seconds

from core.logger import setup_logger
from services.premiere.effects import (
    apply_dip_to_black_fade,
    find_clip_by_timeline_start,
    mute_linked_audio,
)
from services.premiere.pymiere_wrapper import import_files

log = setup_logger("archive_placer")

# Источники manifest, которые трактуем как «архивное видео под факт».
ARCHIVE_SOURCES = {"youtube", "youtube-auto"}


def _pick_cutaway_track_idx(sequence, preferred: Optional[int]) -> int:
    """Свободная верхняя видеодорожка под накладку (cutaway).

    Если preferred задан и существует — берём его. Иначе ищем самую верхнюю
    дорожку без клипов; если все заняты — берём последнюю (Premiere сам
    создаёт дорожку при overwrite за пределами).
    """
    n = sequence.videoTracks.numTracks
    if preferred is not None and 0 <= preferred < n:
        return preferred
    for i in range(n - 1, -1, -1):
        if sequence.videoTracks[i].clips.numItems == 0:
            return i
    return n - 1


def place_archive_clips(
    sequence,
    manifest: Dict[str, dict],
    scene_timings: Dict[str, dict],
    project_dir: Path,
    *,
    track_idx: Optional[int] = None,
    max_clip_sec: float = 8.0,
    fade_in_sec: float = 0.3,
    fade_out_sec: float = 0.3,
) -> int:
    """Расставляет архивные видео-клипы из manifest по слотам их сцен.

    Returns кол-во успешно размещённых клипов.

    manifest[sid] = {"path", "kind": "video", "source": "youtube-auto"|"youtube", ...}
        path — относительный к project_dir (как пишет Stage 4).
    scene_timings[sid] = {"start": float, "end": float, ...}  (alignment["scenes"]).
    """
    # отбираем только архивные видео, у которых есть тайминг сцены
    jobs = []
    for sid, mani in manifest.items():
        if mani.get("kind") != "video" or mani.get("source") not in ARCHIVE_SOURCES:
            continue
        timing = scene_timings.get(sid)
        if not timing:
            log.warning(f"  {sid}: архивный клип есть, но нет тайминга сцены — пропуск")
            continue
        clip_path = (project_dir / mani["path"]).resolve()
        if not clip_path.exists():
            log.warning(f"  {sid}: файл клипа не найден ({clip_path})")
            continue
        jobs.append((sid, mani, timing, clip_path))

    if not jobs:
        log.info("Архивных видео-клипов для укладки нет")
        return 0

    idx = _pick_cutaway_track_idx(sequence, track_idx)
    track = sequence.videoTracks[idx]
    log.info(f"Укладываю {len(jobs)} архив-клип(ов) на V{idx + 1} (cutaway)")

    # импорт всех клипов одним пакетом
    imported = import_files([j[3] for j in jobs])
    by_name = {it.name: it for it in imported}

    placed = 0
    for sid, mani, timing, clip_path in jobs:
        item = by_name.get(clip_path.name) or by_name.get(clip_path.stem)
        if item is None:
            log.warning(f"  {sid}: импортированный item не найден ({clip_path.name})")
            continue

        start = float(timing["start"])
        scene_len = max(0.5, float(timing["end"]) - start)
        target_len = min(scene_len, max_clip_sec)

        try:
            track.overwriteClip(item, time_from_seconds(start))
        except Exception as e:
            log.warning(f"  {sid}: overwriteClip упал на {start:.2f}s: {e}")
            continue

        clip = find_clip_by_timeline_start(track, start)
        if clip is None:
            log.warning(f"  {sid}: не нашёл размещённый клип на {start:.2f}s")
            placed += 1  # клип всё же лёг, просто без пост-обработки
            continue

        # тримим до окна сцены / max (clip.end = трим хвоста)
        natural_len = clip.end.seconds - clip.start.seconds
        if natural_len > target_len + 0.05:
            try:
                clip.end = time_from_seconds(start + target_len)
            except Exception as e:
                log.warning(f"  {sid}: трим до {target_len:.2f}s не вышел: {e}")

        mute_linked_audio(clip)
        apply_dip_to_black_fade(
            clip,
            fade_in_sec=fade_in_sec,
            fade_out_sec=fade_out_sec,
            do_fade_in=True,
            do_fade_out=True,
        )

        placed += 1
        log.info(
            f"  V{idx + 1} ← {sid}: '{mani.get('query', '')[:40]}' "
            f"@{start:.2f}s len={target_len:.2f}s ({clip_path.name})"
        )

    return placed
