"""
services/premiere/level_card_placer.py
Размещает iceberg level title cards на V4 при смене level.

Логика:
1. Сканируем scenes по level — находим переходы вверх (level: 0 → 1, 1 → 2, ...)
2. Для каждого перехода рендерим card .mov (через services.text.level_card)
3. Импортируем все .mov одним пакетом
4. Кладём на V4 на конце предыдущей сцены (в драматической паузе TTS)
   и затемняем V1 на этот момент для cinematic эффекта.
"""
from pathlib import Path
from typing import Dict, List, Optional

from pymiere.wrappers import time_from_seconds

from core.logger import setup_logger
from services.premiere.effects import apply_opacity_dip, find_clip_by_timeline_start
from services.premiere.pymiere_wrapper import ensure_video_tracks, import_files
from services.text.level_card import (
    FADE_IN_SEC as LVL_FADE_IN_SEC,
    FADE_OUT_SEC as LVL_FADE_OUT_SEC,
    HOLD_SEC as LVL_HOLD_SEC,
    render_level_card,
)

log = setup_logger("level_card_placer")


def place_level_overlays(
    sequence,
    scenes: List[Dict],
    butt_timings: Dict[str, Dict],
    project_dir: Path,
    frame_w: int = 1920,
    frame_h: int = 1080,
    level_titles: Optional[Dict[int, str]] = None,
) -> int:
    """Размещает level title cards на V4 при каждой смене level вверх.

    Returns кол-во размещённых карт.
    """
    if not scenes:
        return 0

    # 1. Find level boundaries (переходы вверх) с указателем на ПРЕДЫДУЩУЮ сцену
    boundaries = []  # list of (prev_scene, new_scene, new_level)
    prev_scene = None
    prev_level = None
    for scene in scenes:
        cur_level = int(scene.get("level", 0))
        if prev_level is not None and cur_level > prev_level and prev_scene is not None:
            boundaries.append((prev_scene, scene, cur_level))
        prev_scene = scene
        prev_level = cur_level

    if not boundaries:
        log.info("Level transitions не найдены — карт не будет")
        return 0
    log.info(
        f"Level transitions: {len(boundaries)} → "
        + ", ".join(f"{p['id']}→{n['id']}@L{lvl}" for p, n, lvl in boundaries)
    )

    # 2. Ensure V4 exists
    if not ensure_video_tracks(sequence, 4):
        log.warning("V4 нет — level cards разместить не могу")
        return 0
    v4 = sequence.videoTracks[3]
    v1 = sequence.videoTracks[0]

    # 3. Render cards — длительность КАЖДОЙ карты равна реальному gap'у между
    # сценами, чтобы заполнить чёрный провал на V1 (а не оставить хвост после fade-out).
    cards_dir = project_dir / "assets" / "level_cards"
    cards_dir.mkdir(parents=True, exist_ok=True)

    min_card_dur = LVL_FADE_IN_SEC + LVL_HOLD_SEC + LVL_FADE_OUT_SEC  # 2.45s baseline

    # (prev_scene, new_scene, level, mov_path, total_dur_sec)
    rendered: List[tuple] = []
    for prev_scene, new_scene, level in boundaries:
        prev_bt = butt_timings.get(prev_scene["id"])
        new_bt = butt_timings.get(new_scene["id"])
        if not prev_bt or not new_bt:
            log.warning(
                f"  level {level}: butt_timings не найден — пропускаю render"
            )
            continue
        gap_sec = float(new_bt["start"]) - float(prev_bt["end"])
        target_dur = max(min_card_dur, gap_sec)
        target_hold = max(LVL_HOLD_SEC, target_dur - LVL_FADE_IN_SEC - LVL_FADE_OUT_SEC)
        # Cache key включает hold чтобы при изменении gap пере-рендер срабатывал
        out_mov = cards_dir / f"level_{level}_h{target_hold:.2f}s.mov"
        subtitle = (level_titles or {}).get(level)

        if not (out_mov.exists() and out_mov.stat().st_size > 1000):
            try:
                _, total_dur = render_level_card(
                    level, out_mov,
                    subtitle_override=subtitle,
                    frame_w=frame_w, frame_h=frame_h,
                    hold_sec=target_hold,
                )
            except Exception as e:
                log.warning(f"  level {level} render failed: {e}")
                continue
        else:
            total_dur = LVL_FADE_IN_SEC + target_hold + LVL_FADE_OUT_SEC
            log.info(f"  level {level}: cache hit ({out_mov.name})")

        rendered.append((prev_scene, new_scene, level, out_mov, total_dur))

    if not rendered:
        log.warning("Ни одна level card не отрендерена")
        return 0

    # 4. Import .mov файлы пакетом
    imported = import_files([m for _, _, _, m, _ in rendered])
    items_by_name = {it.name: it for it in imported}

    placed = 0
    for prev_scene, new_scene, level, mov, level_dur in rendered:
        prev_bt = butt_timings[prev_scene["id"]]
        new_bt = butt_timings[new_scene["id"]]
        prev_end = float(prev_bt["end"])
        new_start = float(new_bt["start"])
        gap = new_start - prev_end
        start_sec = prev_end
        log.info(
            f"  level {level}: gap между {prev_scene['id']} и {new_scene['id']} = {gap:.2f}s, "
            f"карта @{start_sec:.2f}s длительностью {level_dur:.2f}s"
        )

        item = items_by_name.get(mov.name)
        if item is None:
            log.warning(f"  level {level}: импортированный item не найден ({mov.name})")
            continue
        try:
            v4.insertClip(item, time_from_seconds(start_sec))
        except Exception as e:
            log.warning(f"  level {level}: V4.insertClip упал: {e}")
            continue

        # Затемняем V1 на весь период level card — чтобы фон не отвлекал от заголовка
        dip_end = start_sec + level_dur
        v1_clip = (
            find_clip_by_timeline_start(v1, prev_bt["start"])
            or find_clip_by_timeline_start(v1, new_bt["start"])
        )
        if v1_clip is not None:
            apply_opacity_dip(v1_clip, start_sec, dip_end, dim_pct=18.0, fade_sec=0.35)

        placed += 1
        log.info(f"  V4 level[{level}] @{start_sec:.2f}s ({prev_scene['id']}→{new_scene['id']})")

    return placed
