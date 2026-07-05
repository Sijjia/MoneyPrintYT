"""
services/premiere/media_burst_placer.py
Beat-cuts на перечислениях — Caravaggio'вский «о, смотри!»-эффект.

Когда в voiceover идёт enumeration («Азия, Европа, Африка»), на каждое слово
врезается отдельный кадр (стоковая картинка/видео по теме) на ~1с + camera-click
SFX между cuts. Кадры кладутся на V9 (поверх scene's base V1).

Schema entry (scene.media_burst):
    {
        "trigger_word": "Азия",                    // первое слово enumeration'а
        "items": [
            {"keyword": "asia map dark"},
            {"keyword": "europe map dark"},
            {"keyword": "africa map dark"}
        ],
        "item_duration_sec": 1.0,                  // ширина каждого кадра
        "sfx_between": "camera_click"              // SFX между cuts (тип из sfx_placer)
    }

Источник медиа: Pexels images (быстро, надёжно). Можно расширить на Pexels Videos
позже.
"""
import hashlib
import random
from pathlib import Path
from typing import Dict, List, Optional

from pymiere.wrappers import time_from_seconds

from core.config import get_settings
from core.logger import setup_logger
from services.images.pexels import PexelsClient
from services.premiere.effects import find_clip_by_timeline_start
from services.premiere.pymiere_wrapper import ensure_video_tracks, import_files
from services.premiere.sfx import find_sfx_for_type, find_word_timestamp, _try_set_sfx_volume

log = setup_logger("media_burst")

V9_INDEX = 8  # V9 = videoTracks[8]
BURST_SFX_VOLUME = 0.22  # camera-click — слышимый, но не глушит голос


def _item_hash(keyword: str, kind: str) -> str:
    return hashlib.md5(f"{kind}|{keyword}".encode("utf-8")).hexdigest()[:8]


def _fetch_burst_item(
    keyword: str, kind: str, out_path: Path, pexels: PexelsClient,
) -> Optional[Path]:
    """Скачивает один item для burst через Pexels. Returns mp4/jpg path or None."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists() and out_path.stat().st_size > 1000:
        return out_path
    try:
        return pexels.search_and_download(keyword, out_path)
    except Exception as e:
        log.warning(f"  burst fetch '{keyword}' failed: {e}")
        return None


def place_media_bursts(
    sequence,
    scenes: List[Dict],
    whisper_words: List[Dict],
    project_dir: Path,
    sfx_dir: Optional[Path] = None,
    seed: Optional[int] = None,
    frame_w: int = 1920,
    frame_h: int = 1080,
) -> int:
    """Расставляет beat-cuts по scene.media_burst.

    Returns: общее кол-во размещённых burst-кадров (cumulative across scenes).
    """
    # Собираем все media_burst-entries с timestamps
    jobs: List[tuple] = []  # (scene_id, entry, start_timestamp)
    for scene in scenes:
        sid = scene["id"]
        burst = scene.get("media_burst")
        if not burst:
            continue
        trigger = burst.get("trigger_word")
        if not trigger:
            log.warning(f"  {sid}: media_burst без trigger_word")
            continue
        ts = find_word_timestamp(trigger, whisper_words or [])
        if ts is None:
            log.warning(f"  {sid}: media_burst trigger '{trigger}' не найден в whisper-words")
            continue
        items = burst.get("items") or []
        if not items:
            continue
        jobs.append((sid, burst, ts))

    if not jobs:
        log.info("В scenes.json нет media_burst-entries (или ни один trigger не найден)")
        return 0

    # Lazy init
    try:
        pexels = PexelsClient()
    except Exception as e:
        log.warning(f"PexelsClient init failed ({e}) — media_burst пропускаю")
        return 0

    # Ensure V9 (индекс 8) + кэш-директория
    if not ensure_video_tracks(sequence, V9_INDEX + 1):
        log.warning("V9 track создать не получилось — media_burst пропускаю")
        return 0
    v9 = sequence.videoTracks[V9_INDEX]
    burst_dir = project_dir / "assets" / "media_burst"
    burst_dir.mkdir(parents=True, exist_ok=True)

    # Подготовка SFX (camera-click и аналоги) — лениво
    sfx_files_by_type: Dict[str, List[Path]] = {}
    a3 = None
    audio_tracks = sequence.audioTracks
    if sfx_dir and audio_tracks.numTracks >= 3:
        a3 = audio_tracks[2]

    rng = random.Random(seed)
    total_placed = 0

    for sid, burst, ts in jobs:
        items = burst.get("items") or []
        item_dur = float(burst.get("item_duration_sec", 1.0))
        sfx_between_type = burst.get("sfx_between") or "camera_click"

        # 1. Фетчим все items этого burst
        fetched: List[tuple] = []  # (item_dict, local_path)
        for idx, item in enumerate(items):
            keyword = item.get("keyword")
            if not keyword:
                continue
            h = _item_hash(keyword, "image")
            # Pexels возвращает jpg
            ext = ".jpg"
            local = burst_dir / f"{sid}_burst{idx}_{h}{ext}"
            if local.exists() and local.stat().st_size > 1000:
                fetched.append((item, local))
                continue
            downloaded = _fetch_burst_item(keyword, "image", local, pexels)
            if downloaded:
                fetched.append((item, downloaded))

        if not fetched:
            log.warning(f"  {sid}: ни один burst item не скачался")
            continue

        # 2. Импортируем пачкой
        imported = import_files([p for _, p in fetched])
        items_by_name = {it.name: it for it in imported}

        # 3. Размещаем на V9 — каждый item начиная с ts + i*item_dur
        placed_this_burst = 0
        for i, (item, local) in enumerate(fetched):
            cur_start = ts + i * item_dur
            project_item = items_by_name.get(local.name)
            if project_item is None:
                log.warning(f"  {sid}: burst[{i}] не нашёл импортированный item ({local.name})")
                continue
            try:
                v9.insertClip(project_item, time_from_seconds(cur_start))
            except Exception as e:
                log.warning(f"  {sid}: burst[{i}] V9.insertClip failed: {e}")
                continue
            clip = find_clip_by_timeline_start(v9, cur_start)
            if clip is not None:
                try:
                    clip.end = time_from_seconds(cur_start + item_dur)
                except Exception:
                    pass
            placed_this_burst += 1
            log.info(
                f"  V9 {sid}: burst[{i}] '{item.get('keyword')}' @{cur_start:.2f}s "
                f"(+{item_dur:.2f}s) → {local.name}"
            )

        # 4. SFX между cuts на A3 — на стыке cur_start между item[i-1] и item[i]
        if a3 is not None and sfx_dir and placed_this_burst > 1:
            if sfx_between_type not in sfx_files_by_type:
                sfx_files_by_type[sfx_between_type] = find_sfx_for_type(sfx_between_type, Path(sfx_dir))
            sfx_pool = sfx_files_by_type[sfx_between_type]
            if sfx_pool:
                for i in range(1, placed_this_burst):
                    cut_ts = ts + i * item_dur
                    picked = rng.choice(sfx_pool)
                    try:
                        sfx_imported = import_files([picked])
                        if not sfx_imported:
                            continue
                        sfx_item = sfx_imported[0]
                        a3.insertClip(sfx_item, time_from_seconds(cut_ts))
                        sfx_clip = find_clip_by_timeline_start(a3, cut_ts)
                        if sfx_clip is not None:
                            _try_set_sfx_volume(sfx_clip, BURST_SFX_VOLUME)
                        log.info(
                            f"  A3 {sid}: burst-SFX '{sfx_between_type}' @{cut_ts:.2f}s "
                            f"→ {picked.name}"
                        )
                    except Exception as e:
                        log.warning(f"  {sid}: burst-SFX @{cut_ts:.2f}s failed: {e}")

        total_placed += placed_this_burst

    return total_placed
