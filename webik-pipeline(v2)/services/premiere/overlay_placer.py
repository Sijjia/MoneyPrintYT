"""
services/premiere/overlay_placer.py
Расстановка динамических оверлеев (StatPop/NameLabel/KineticPhrase, отрендеренные
Remotion в прозрачные MOV) на верхнюю свободную видеодорожку в их таймкоды.

Оверлеи с альфой → Premiere композитит их поверх тела автоматически. Вход/выход
анимации уже вшиты в саму композицию, поэтому здесь НЕ добавляем фейды и не трогаем
масштаб. Звука у оверлеев нет; на всякий случай мьютим линкованное.

Вход: overlays_rendered.json → [{id, composition, start, duration_sec, file, props}].
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from pymiere.wrappers import time_from_seconds

from core.logger import setup_logger
from services.premiere.effects import find_clip_by_timeline_start, mute_linked_audio
from services.premiere.pymiere_wrapper import import_files

log = setup_logger("overlay_placer")


def _pick_top_free_track(sequence, preferred: Optional[int]) -> int:
    """Верхняя свободная видеодорожка (оверлеи должны быть выше всего)."""
    n = sequence.videoTracks.numTracks
    if preferred is not None and 0 <= preferred < n:
        return preferred
    for i in range(n - 1, -1, -1):
        if sequence.videoTracks[i].clips.numItems == 0:
            return i
    return n - 1


def place_overlays(
    sequence,
    rendered_overlays: List[dict],
    project_dir: Path,
    *,
    track_idx: Optional[int] = None,
) -> int:
    """Кладёт отрендеренные оверлеи на свободную верхнюю дорожку. Возвращает кол-во."""
    jobs = []
    for ov in rendered_overlays:
        raw = Path(ov.get("file", ""))
        # путь в манифесте относителен CWD (корень webik); пробуем несколько баз
        candidates = [raw] if raw.is_absolute() else [
            Path.cwd() / raw,
            project_dir / raw,
            project_dir / "assets" / "overlays" / f"{ov['id']}.mov",
        ]
        f = next((c.resolve() for c in candidates if c.exists()), None)
        if f is None:
            log.warning(f"  {ov['id']}: MOV не найден ({raw})")
            continue
        jobs.append((ov, f))

    if not jobs:
        log.info("Оверлеев для укладки нет")
        return 0

    idx = _pick_top_free_track(sequence, track_idx)
    track = sequence.videoTracks[idx]
    log.info(f"Кладу {len(jobs)} оверлей(ев) на V{idx + 1} (альфа-композит)")

    imported = import_files([f for _, f in jobs])
    by_name = {it.name: it for it in imported}

    placed = 0
    for ov, f in jobs:
        item = by_name.get(f.name) or by_name.get(f.stem)
        if item is None:
            log.warning(f"  {ov['id']}: импортированный item не найден ({f.name})")
            continue

        start = float(ov["start"])
        try:
            track.overwriteClip(item, time_from_seconds(start))
        except Exception as e:
            log.warning(f"  {ov['id']}: overwriteClip упал на {start:.2f}s: {e}")
            continue

        clip = find_clip_by_timeline_start(track, start)
        if clip is not None:
            try:
                mute_linked_audio(clip)
            except Exception:
                pass

        placed += 1
        p = ov.get("props", {})
        desc = p.get("value") or p.get("name") or p.get("phrase") or ""
        log.info(f"  V{idx + 1} ← {ov['id']} [{ov.get('type', 'scene')}] @{start:.2f}s '{desc}'")

    log.info(f"Уложено {placed}/{len(jobs)} оверлеев")
    return placed
