"""
services/premiere/mascot.py
Размещение маскота-капибары «бебрик» на V2 поверх climactic-сцен.

Маскот — это .mov с чёрным фоном (не альфа). Используется blend mode = Screen,
чтобы убрать чёрные пиксели визуально (Screen blend: чёрные пиксели прозрачные,
светлые накладываются по lightening-формуле).
"""
from pathlib import Path
from typing import Dict, List, Optional

import pymiere
from pymiere.wrappers import time_from_seconds

from core.logger import setup_logger
from services.premiere.effects import (
    _find_component,
    _find_property,
    find_clip_by_timeline_start,
)
from services.premiere.pymiere_wrapper import import_files

log = setup_logger("mascot")

# Длительность маскота в секундах от начала climactic-сцены
MASCOT_DURATION_SEC = 3.0

# Scale в процентах. Если bebrik исходник 1920x1080 — scale 40% даёт ~768x432 в frame.
MASCOT_SCALE_PCT = 40.0

# Позиция центра маскота в координатах frame (1920x1080).
# (1500, 810) ≈ нижний-правый угол с отступом.
MASCOT_POSITION_X = 1500.0
MASCOT_POSITION_Y = 810.0

# Premiere blend mode index: Screen = 6 в большинстве версий
# Список: 0=Normal,1=Dissolve,2=Darken,3=Multiply,4=ColorBurn,5=LinearBurn,
#         6=Screen, 7=Lighten, 8=ColorDodge, 9=LinearDodge(Add), ...
BLEND_MODE_SCREEN = 6


def place_mascots(
    sequence,
    scenes: List[Dict],
    scene_timings: Dict[str, Dict],
    mascot_path: Path,
) -> int:
    """Расставляет маскот на climactic-сценах. Возвращает количество размещённых.

    Делает best-effort: если что-то из (blend mode / scale / position) не сработает —
    логирует warning и продолжает. Главное — clip оказывается на V2 в правильное время.
    """
    if not mascot_path or not Path(mascot_path).exists():
        log.info(f"Mascot не найден ({mascot_path}), пропускаю")
        return 0

    climactic_scenes = [s for s in scenes if s.get("mood") == "climactic"]
    if not climactic_scenes:
        log.info("Нет сцен с mood=climactic, маскот не нужен")
        return 0

    # 1. Импортируем bebrik один раз
    mascot_items = import_files([Path(mascot_path)])
    if not mascot_items:
        log.warning(f"Не удалось импортировать {mascot_path}")
        return 0
    bebrik_item = mascot_items[0]
    log.info(f"Маскот импортирован: {bebrik_item.name}")

    # 2. Гарантируем что есть V2
    video_tracks = sequence.videoTracks
    if video_tracks.numTracks < 2:
        log.warning(f"В sequence только {video_tracks.numTracks} video track(ов), V2 нет — маскот не положу")
        return 0
    v2 = sequence.videoTracks[1]

    placed = 0
    for scene in climactic_scenes:
        sid = scene["id"]
        timing = scene_timings.get(sid)
        if not timing:
            log.warning(f"  {sid}: нет timing, пропускаю маскот")
            continue

        start_sec = float(timing["start"])
        scene_dur = float(timing["end"]) - start_sec
        bebrik_dur = min(MASCOT_DURATION_SEC, max(0.1, scene_dur - 0.2))

        # Insert на V2
        try:
            v2.insertClip(bebrik_item, time_from_seconds(start_sec))
        except Exception as e:
            log.warning(f"  {sid}: insertClip упал: {e}")
            continue

        clip = find_clip_by_timeline_start(v2, start_sec)
        if clip is None:
            log.warning(f"  {sid}: не нашёл вставленный mascot clip")
            continue

        # Trim длительности
        try:
            clip.end = time_from_seconds(start_sec + bebrik_dur)
        except Exception as e:
            log.warning(f"  {sid}: не смог trim mascot до {bebrik_dur:.2f}s: {e}")

        # Scale + Position через Motion property
        _try_set_motion(clip, MASCOT_SCALE_PCT, MASCOT_POSITION_X, MASCOT_POSITION_Y, sid)

        # Blend Mode = Screen через Opacity component
        _try_set_blend_mode(clip, BLEND_MODE_SCREEN, sid)

        placed += 1
        log.info(
            f"  V2 {sid}: маскот {start_sec:.2f}s→{start_sec + bebrik_dur:.2f}s "
            f"(scale={MASCOT_SCALE_PCT}%, pos=({MASCOT_POSITION_X:.0f},{MASCOT_POSITION_Y:.0f}))"
        )

    return placed


def _try_set_motion(clip, scale_pct: float, pos_x: float, pos_y: float, sid: str):
    motion = _find_component(clip, "Motion")
    if motion is None:
        log.warning(f"  {sid}: Motion компонент не найден")
        return

    scale_prop = _find_property(motion, "Scale")
    if scale_prop is not None:
        try:
            scale_prop.setValue(float(scale_pct), True)
        except Exception as e:
            log.warning(f"  {sid}: Scale.setValue упал: {e}")

    pos_prop = _find_property(motion, "Position")
    if pos_prop is not None:
        # Position — Point2D, ожидает array [x, y] в нормализованных координатах [0,1]
        # или в абсолютных пикселях. В большинстве JSX-примеров — нормализованные.
        # Для frame 1920x1080: (1500, 810) → (0.781, 0.75)
        norm_x = pos_x / 1920.0
        norm_y = pos_y / 1080.0
        for value in ([norm_x, norm_y], [pos_x, pos_y]):
            try:
                pos_prop.setValue(value, True)
                break
            except Exception as e:
                log.debug(f"  {sid}: Position.setValue({value}) failed: {e}")
        else:
            log.warning(f"  {sid}: Position.setValue не сработал ни в одном формате")


def _try_set_blend_mode(clip, blend_mode_index: int, sid: str):
    """Установить blend mode у компонента Opacity.

    В Premiere Blend Mode — это property компонента Opacity с числовым enum value.
    """
    opacity_comp = _find_component(clip, "Opacity")
    if opacity_comp is None:
        log.warning(f"  {sid}: Opacity component не найден (blend mode не установлен)")
        return

    blend_prop = _find_property(opacity_comp, "Blend Mode")
    if blend_prop is None:
        # В некоторых версиях называется иначе
        for alt in ["blendMode", "Blending Mode", "Mode"]:
            blend_prop = _find_property(opacity_comp, alt)
            if blend_prop is not None:
                break
    if blend_prop is None:
        log.warning(f"  {sid}: Blend Mode property не найдена в Opacity")
        return

    try:
        blend_prop.setValue(int(blend_mode_index), True)
    except Exception as e:
        log.warning(f"  {sid}: Blend Mode.setValue({blend_mode_index}) упал: {e}")
