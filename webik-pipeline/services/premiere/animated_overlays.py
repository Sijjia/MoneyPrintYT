"""
services/premiere/animated_overlays.py
Постоянные animated overlays на V5 — film grain / dust поверх всего видео.

Логика:
1. Берём готовый dust/grain .mp4 из Pack media
2. Делаем audio-free копию (ffmpeg stream copy)
3. На V5 кладём loop через всю длительность sequence
4. Opacity ~15-20%, blend mode Screen — затемнённое исчезает, светлая «зернистость» поверх

Light leaks вспышки на ключевых моментах (level transitions / SFX hits) — TODO.
"""
from pathlib import Path
from typing import Optional

from pymiere.wrappers import time_from_seconds

from core.logger import setup_logger
from services.premiere.effects import (
    BLEND_SCREEN,
    apply_blend_mode,
    apply_static_opacity,
    apply_static_scale,
    compute_fit_scale_pct,
    find_clip_by_timeline_start,
)
from services.premiere.pymiere_wrapper import ensure_video_tracks, import_files


def _probe_size(path: Path) -> tuple[int, int]:
    """Возвращает (w, h) видео или (0, 0) при ошибке."""
    try:
        import ffmpeg
        probe = ffmpeg.probe(str(path))
        for stream in probe.get("streams", []):
            if stream.get("codec_type") == "video":
                return int(stream.get("width", 0)), int(stream.get("height", 0))
    except Exception:
        pass
    return 0, 0

log = setup_logger("animated_overlays")

# Дефолтные ассеты — лежат в Pack media
DUST_GRAIN_PATHS = [
    Path(r"E:\YouTube Webik\Pack media\Animated Textures\Dust Texture.mp4"),
]
LIGHT_LEAK_PATHS = [
    Path(r"E:\YouTube Webik\Pack media\Flim Burns\04356_light_leaks_element_366_wwwcutestockfootagecom (Original).mp4"),
]

GRAIN_OPACITY_PCT = 6.0       # 2026-05-12 снижено с 18% — user сказал «не корректно появляется»
LIGHT_LEAK_OPACITY_PCT = 12.0  # 2026-05-12 снижено с 35% — слишком в лоб
LIGHT_LEAK_DURATION = 1.6  # на cut


def _strip_audio_copy(src: Path, out: Path) -> Optional[Path]:
    """ffmpeg stream-copy без audio."""
    if out.exists() and out.stat().st_size > 1000:
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        import ffmpeg
        (
            ffmpeg.input(str(src))
            .output(str(out), vcodec="copy", an=None)
            .overwrite_output()
            .global_args("-loglevel", "error")
            .run(quiet=True)
        )
        return out
    except Exception as e:
        log.warning(f"strip audio overlay failed для {src.name}: {e}")
        return None


def _first_existing(paths) -> Optional[Path]:
    for p in paths:
        if p.exists():
            return p
    return None


def place_grain_overlay(
    sequence,
    total_duration_sec: float,
    project_dir: Path,
    frame_w: int = 1920,
    frame_h: int = 1080,
) -> int:
    """Кладёт film-grain/dust loop на V5 через всю длительность.

    Returns кол-во клипов размещено (>=1 если успех).
    """
    src = _first_existing(DUST_GRAIN_PATHS)
    if src is None:
        log.warning("Dust/grain overlay не найден — пропускаю")
        return 0

    if not ensure_video_tracks(sequence, 5):
        log.warning("V5 нет — grain overlay пропускаю")
        return 0
    v5 = sequence.videoTracks[4]

    overlays_dir = project_dir / "assets" / "overlays_silent"
    silent = _strip_audio_copy(src, overlays_dir / src.name)
    if silent is None:
        return 0

    items = import_files([silent])
    if not items:
        return 0
    item = items[0]
    iw, ih = _probe_size(silent)
    fit_pct = compute_fit_scale_pct(iw, ih, frame_w, frame_h) if iw and ih else 100.0

    try:
        clip_dur = float(item.getOutPoint().seconds - item.getInPoint().seconds)
    except Exception:
        clip_dur = 0.0
    if clip_dur <= 0.1:
        clip_dur = 10.0

    log.info(
        f"Grain overlay: {src.name} ({iw}x{ih}, fit={fit_pct:.0f}%, dur={clip_dur:.1f}s) "
        f"→ V5 до {total_duration_sec:.1f}s"
    )

    placed = 0
    cur = 0.0
    safety = 0
    last_clip = None
    while cur < total_duration_sec and safety < 60:
        try:
            v5.insertClip(item, time_from_seconds(cur))
        except Exception as e:
            log.warning(f"  grain insertClip @{cur:.2f}s: {e}")
            break
        clip = find_clip_by_timeline_start(v5, cur)
        if clip is None:
            log.warning(f"  grain clip @{cur:.2f}s не найден после insertClip")
            break
        apply_static_scale(clip, fit_pct)
        apply_static_opacity(clip, GRAIN_OPACITY_PCT)
        apply_blend_mode(clip, BLEND_SCREEN)
        actual_dur = max(0.5, clip.duration.seconds)
        last_clip = clip
        cur += actual_dur
        placed += 1
        safety += 1

    # Обрезаем последний loop до total_duration_sec, чтобы зерно не вытекало
    # за границу контента (V5 на 46s при содержимом 27s — типичный artifact)
    if last_clip is not None and cur > total_duration_sec:
        try:
            last_clip.end = time_from_seconds(total_duration_sec)
        except Exception as e:
            log.warning(f"  grain trim last clip failed: {e}")

    return placed


def place_vignette_overlay(
    sequence,
    total_duration_sec: float,
    project_dir: Path,
    frame_w: int = 1920,
    frame_h: int = 1080,
) -> int:
    """Вставляет static vignette PNG на V7 через всю длительность.

    Cinematic «затемнение по краям» без полноценного Lumetri.
    """
    if not ensure_video_tracks(sequence, 7):
        log.warning("V7 нет — vignette пропускаю")
        return 0
    v7 = sequence.videoTracks[6]

    from services.visual.vignette import generate_vignette_png
    overlays_dir = project_dir / "assets" / "overlays_silent"
    overlays_dir.mkdir(parents=True, exist_ok=True)
    png = overlays_dir / "vignette.png"
    if not png.exists():
        generate_vignette_png(png, frame_w=frame_w, frame_h=frame_h)

    items = import_files([png])
    if not items:
        return 0
    item = items[0]
    try:
        v7.insertClip(item, time_from_seconds(0.0))
    except Exception as e:
        log.warning(f"vignette insertClip failed: {e}")
        return 0

    clip = find_clip_by_timeline_start(v7, 0.0)
    if clip is None:
        return 0

    # Растянуть PNG до полной длительности через end-point set
    try:
        clip.end = time_from_seconds(total_duration_sec)
    except Exception as e:
        log.warning(f"vignette end set failed: {e}")
    apply_static_opacity(clip, 100.0)
    log.info(f"V7: vignette {total_duration_sec:.1f}s")
    return 1


def place_light_leak_on_cuts(
    sequence,
    cut_points_sec,
    project_dir: Path,
    frame_w: int = 1920,
    frame_h: int = 1080,
) -> int:
    """Light leak вспышка на каждой переданной точке cut.

    cut_points_sec: список абсолютных секунд (например, level transitions).
    Кладётся на V6, чтобы не конфликтовать с V5 grain.
    """
    if not cut_points_sec:
        return 0
    src = _first_existing(LIGHT_LEAK_PATHS)
    if src is None:
        log.warning("Light leak overlay не найден — пропускаю")
        return 0
    if not ensure_video_tracks(sequence, 6):
        return 0
    v6 = sequence.videoTracks[5]

    overlays_dir = project_dir / "assets" / "overlays_silent"
    silent = _strip_audio_copy(src, overlays_dir / src.name)
    if silent is None:
        return 0

    items = import_files([silent])
    if not items:
        return 0
    item = items[0]
    iw, ih = _probe_size(silent)
    fit_pct = compute_fit_scale_pct(iw, ih, frame_w, frame_h) if iw and ih else 100.0

    placed = 0
    for t in cut_points_sec:
        center = float(t)
        start = max(0.0, center - LIGHT_LEAK_DURATION / 2.0)
        try:
            v6.insertClip(item, time_from_seconds(start))
        except Exception as e:
            log.warning(f"  light leak @{start:.2f}: {e}")
            continue
        clip = find_clip_by_timeline_start(v6, start)
        if clip is None:
            continue
        apply_static_scale(clip, fit_pct)
        apply_static_opacity(clip, LIGHT_LEAK_OPACITY_PCT)
        apply_blend_mode(clip, BLEND_SCREEN)
        placed += 1
        log.info(f"  light leak @{start:.2f}s ({src.name}, {iw}x{ih}, fit={fit_pct:.0f}%)")

    return placed
