"""
services/premiere/film_burn.py
Размещение film burn .mov на V2 поверх стыков с типом FILM_BURN.

Film burns — это видео-оверлеи с прожжённой плёнкой и встроенным SFX
(`E:\\YouTube Webik\\Pack media\\FILM BURN (WITH SFX)\\`). Применяются с blend
mode = Screen: чёрный фон становится прозрачным, светлые «искры» накладываются
поверх V1.

Что не делаем сейчас:
- Точная синхронизация SFX с beat в музыке
- Cropping/scale если burn не в 1080p
- Множественный V2-pass (если стыков FILM_BURN несколько подряд — могут перекрыться)
"""
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pymiere.wrappers import time_from_seconds
import ffmpeg

from core.logger import setup_logger
from services.premiere.effects import (
    _find_component,
    _find_property,
    find_clip_by_timeline_start,
)
from services.premiere.pymiere_wrapper import import_files

log = setup_logger("film_burn")

FILM_BURN_BLEND_MODE_SCREEN = 6
DEFAULT_BURN_DURATION_SEC = 0.6  # fallback если ffprobe не сработал


def find_film_burns(film_burn_dir: Optional[Path]) -> List[Path]:
    """Возвращает отсортированный список .mp4/.mov файлов в папке (нерекурсивно)."""
    if not film_burn_dir:
        return []
    p = Path(film_burn_dir)
    if not p.exists() or not p.is_dir():
        return []
    return sorted(
        f for f in p.iterdir()
        if f.is_file() and f.suffix.lower() in (".mp4", ".mov", ".mkv", ".avi")
    )


def get_video_duration(path: Path) -> float:
    try:
        probe = ffmpeg.probe(str(path))
        return float(probe["format"]["duration"])
    except Exception as e:
        log.warning(f"ffprobe не смог прочитать {path.name}: {e}, использую {DEFAULT_BURN_DURATION_SEC}s")
        return DEFAULT_BURN_DURATION_SEC


def place_film_burns(
    sequence,
    scenes: List[Dict],
    butt_timings: Dict[str, Dict],
    fade_pairs: List[Tuple],
    film_burn_dir: Optional[Path],
    seed: Optional[int] = None,
) -> int:
    """Кладёт film burn на V2 на каждом стыке где fade_pairs[i].t_out == FILM_BURN.

    Args:
        sequence: pymiere Sequence
        scenes: список сцен из scenes.json
        butt_timings: {scene_id: {start, end}} — butt-joined тайминги, end_i = cut point i→i+1
        fade_pairs: [(fade_in, fade_out, t_in, t_out), ...] из transitions.choose_transition_type
        film_burn_dir: папка с .mov / .mp4 файлами
        seed: для воспроизводимого выбора рандомного burn (например hash(project_id))

    Returns:
        Кол-во размещённых film burn'ов.
    """
    burns = find_film_burns(film_burn_dir)
    if not burns:
        log.info(f"Film burn'ов не найдено в {film_burn_dir}")
        return 0
    log.info(f"Найдено {len(burns)} film burn файлов")

    # Какие стыки — FILM_BURN
    burn_stitches: List[Tuple[int, float]] = []
    n = len(scenes)
    for i, fp in enumerate(fade_pairs):
        if i >= n - 1:
            continue  # последний clip — нет следующего стыка
        _, _, _, t_out = fp
        if t_out.value != "film_burn":
            continue
        sid = scenes[i]["id"]
        bt = butt_timings.get(sid)
        if not bt:
            continue
        cut_point_sec = float(bt["end"])
        burn_stitches.append((i, cut_point_sec))

    if not burn_stitches:
        log.info("Нет FILM_BURN стыков, пропускаю")
        return 0

    # Гарантируем V2
    video_tracks = sequence.videoTracks
    if video_tracks.numTracks < 2:
        log.warning(f"V2 нет в sequence ({video_tracks.numTracks} tracks) — film burn не положу")
        return 0
    v2 = video_tracks[1]

    rng = random.Random(seed)
    placed = 0

    for stitch_idx, cut_point_sec in burn_stitches:
        burn_path = rng.choice(burns)
        burn_dur = get_video_duration(burn_path)
        burn_start = max(0.0, cut_point_sec - burn_dur / 2.0)

        items = import_files([burn_path])
        if not items:
            log.warning(f"Не смог импортировать {burn_path.name}")
            continue
        burn_item = items[0]

        try:
            v2.insertClip(burn_item, time_from_seconds(burn_start))
        except Exception as e:
            log.warning(f"V2.insertClip film burn упал: {e}")
            continue

        clip = find_clip_by_timeline_start(v2, burn_start)
        if clip is None:
            log.warning(f"Не нашёл вставленный film burn clip @{burn_start:.2f}s")
            continue

        # Blend Mode = Screen
        opacity_comp = _find_component(clip, "Opacity")
        if opacity_comp is not None:
            blend_prop = _find_property(opacity_comp, "Blend Mode")
            if blend_prop is None:
                for alt in ["blendMode", "Blending Mode", "Mode"]:
                    blend_prop = _find_property(opacity_comp, alt)
                    if blend_prop is not None:
                        break
            if blend_prop is not None:
                try:
                    blend_prop.setValue(FILM_BURN_BLEND_MODE_SCREEN, True)
                except Exception as e:
                    log.warning(f"Blend Mode setValue упал: {e}")

        placed += 1
        log.info(
            f"  V2 burn: cut={cut_point_sec:.2f}s, range={burn_start:.2f}s→"
            f"{burn_start + burn_dur:.2f}s, file={burn_path.name}"
        )

    return placed
