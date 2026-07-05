"""
services/premiere/chart_placer.py
Расставляет анимированные чарты (counter / donut / rank_bar) на V8.

Логика:
1. Для каждой scene.charts[] entry — найти trigger_word timestamp в whisper-words
2. Собрать ChartSpec из entry
3. Pre-render .mov с alpha (cached по content-hash)
4. Ensure V8 трек существует, insertClip @timestamp
5. Trim clip end к total_duration_sec чтобы чарт не вылезал за конец видео

Schema entry (в scenes.json scene.charts[]):
    {
        "kind": "counter" | "percentage_donut" | "rank_bar",
        "trigger_word": "Кореи",         # точное слово где появится чарт
        "duration_sec": 4.0,
        "label": "...",
        "accent_color": "#ff5050",
        // counter:
        "counter_target": 40000000,
        "counter_format": "int_thousands",
        "counter_suffix": "",
        // donut:
        "donut_percent": 3.0,
        // rank_bar:
        "rank_items": [["США", 80], ["Корея", 95]],
        "rank_highlight_index": 1
    }
"""
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional

from pymiere.wrappers import time_from_seconds

from core.logger import setup_logger
from services.charts.chart_renderer import ChartSpec, render_chart
from services.premiere.effects import find_clip_by_timeline_start
from services.premiere.pymiere_wrapper import ensure_video_tracks, import_files
from services.premiere.sfx import find_word_timestamp

log = setup_logger("chart_placer")

# V8 = индекс 7 (V1=0). Ставим чарт ПОВЕРХ entity/level card но ПОД vignette.
V8_INDEX = 7


def _spec_from_entry(entry: Dict) -> ChartSpec:
    rank_items = []
    for item in (entry.get("rank_items") or []):
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            rank_items.append((str(item[0]), float(item[1])))

    timeline_events = []
    for item in (entry.get("timeline_events") or []):
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            timeline_events.append((str(item[0]), str(item[1])))

    map_arrows = []
    for item in (entry.get("map_arrows") or []):
        # Принимаем dict или list-of-3 формат
        if isinstance(item, dict):
            f = item.get("from") or [50, 50]
            t = item.get("to") or [50, 50]
            lbl = item.get("label", "")
        elif isinstance(item, (list, tuple)) and len(item) >= 3:
            f, t, lbl = item[0], item[1], item[2]
        else:
            continue
        try:
            from_xy = (float(f[0]), float(f[1]))
            to_xy = (float(t[0]), float(t[1]))
            map_arrows.append((from_xy, to_xy, str(lbl)))
        except Exception:
            continue

    iceberg_levels = [str(x) for x in (entry.get("iceberg_levels") or [])]

    return ChartSpec(
        kind=str(entry.get("kind", "counter")),
        duration_sec=float(entry.get("duration_sec", 4.0)),
        label=str(entry.get("label", "")),
        sublabel=str(entry.get("sublabel", "")),
        color=str(entry.get("color", "#ffffff")),
        accent_color=str(entry.get("accent_color", "#ff5050")),
        counter_target=float(entry.get("counter_target", 0.0)),
        counter_format=str(entry.get("counter_format", "int")),
        counter_suffix=str(entry.get("counter_suffix", "")),
        donut_percent=float(entry.get("donut_percent", 0.0)),
        rank_items=rank_items,
        rank_highlight_index=int(entry.get("rank_highlight_index", 0)),
        timeline_events=timeline_events,
        map_arrows=map_arrows,
        map_origin_label=str(entry.get("map_origin_label", "")),
        iceberg_levels=iceberg_levels,
        iceberg_current_level=int(entry.get("iceberg_current_level", 0)),
    )


def _content_hash(spec: ChartSpec) -> str:
    """Hash spec'а для cache-key. Меняется только при изменении контента → re-render."""
    payload = json.dumps({
        "k": spec.kind, "d": round(spec.duration_sec, 2),
        "l": spec.label, "s": spec.sublabel,
        "c": spec.color, "a": spec.accent_color,
        "ct": spec.counter_target, "cf": spec.counter_format, "cs": spec.counter_suffix,
        "dp": spec.donut_percent,
        "ri": [[n, v] for n, v in spec.rank_items], "rh": spec.rank_highlight_index,
        "te": [[a, b] for a, b in spec.timeline_events],
        "ma": [[list(f), list(t), l] for f, t, l in spec.map_arrows],
        "mo": spec.map_origin_label,
        "il": list(spec.iceberg_levels), "ic": spec.iceberg_current_level,
    }, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(payload.encode("utf-8")).hexdigest()[:8]


def place_charts(
    sequence,
    scenes: List[Dict],
    whisper_words: List[Dict],
    project_dir: Path,
    total_duration_sec: float,
    frame_w: int = 1920,
    frame_h: int = 1080,
) -> int:
    """Расставляет .mov-чарты на V8 по scene.charts[].trigger_word.

    Returns: кол-во размещённых чартов.
    """
    # Собираем все chart-entries с timestamps
    jobs: List[tuple] = []  # (sid, idx, entry, timestamp)
    for scene in scenes:
        sid = scene["id"]
        for idx, entry in enumerate(scene.get("charts") or []):
            trigger = entry.get("trigger_word")
            if not trigger:
                log.warning(f"  {sid}: chart[{idx}] без trigger_word — пропускаю")
                continue
            ts = find_word_timestamp(trigger, whisper_words or [])
            if ts is None:
                log.warning(f"  {sid}: chart[{idx}] trigger '{trigger}' не найден в whisper-words")
                continue
            jobs.append((sid, idx, entry, ts))

    if not jobs:
        log.info("В scenes.json нет chart-entries (или ни один trigger не найден)")
        return 0

    # Render каждый чарт (с cache)
    charts_dir = project_dir / "assets" / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)
    rendered: List[tuple] = []  # (sid, idx, entry, timestamp, mov_path, dur_sec)
    for sid, idx, entry, ts in jobs:
        spec = _spec_from_entry(entry)
        h = _content_hash(spec)
        out_mov = charts_dir / f"{sid}_chart{idx}_{spec.kind}_{h}.mov"
        if out_mov.exists() and out_mov.stat().st_size > 1000:
            log.info(f"  {sid}: chart[{idx}] cache hit ({out_mov.name})")
            dur = spec.duration_sec
        else:
            try:
                _, dur = render_chart(spec, out_mov, frame_w=frame_w, frame_h=frame_h)
            except Exception as e:
                log.warning(f"  {sid}: chart[{idx}] render failed: {e}")
                continue
        rendered.append((sid, idx, entry, ts, out_mov, dur))

    if not rendered:
        log.warning("Ни один чарт не отрендерился")
        return 0

    # Ensure V8 (индекс 7)
    if not ensure_video_tracks(sequence, V8_INDEX + 1):
        log.warning("V8 track создать не получилось — чарты не размещаю")
        return 0
    v8 = sequence.videoTracks[V8_INDEX]

    # Import + place
    imported = import_files([m for _, _, _, _, m, _ in rendered])
    items_by_name = {it.name: it for it in imported}

    placed = 0
    for sid, idx, entry, ts, mov_path, dur in rendered:
        item = items_by_name.get(mov_path.name) or items_by_name.get(mov_path.stem)
        if item is None:
            log.warning(f"  {sid}: chart[{idx}] импортированный item не найден ({mov_path.name})")
            continue
        try:
            v8.insertClip(item, time_from_seconds(ts))
        except Exception as e:
            log.warning(f"  {sid}: chart[{idx}] V8.insertClip упал: {e}")
            continue

        # Trim чтобы не вылез за конец видео
        clip = find_clip_by_timeline_start(v8, ts)
        if clip is not None:
            try:
                natural_end = clip.end.seconds
                if natural_end > total_duration_sec:
                    clip.end = time_from_seconds(total_duration_sec)
            except Exception:
                pass

        placed += 1
        log.info(
            f"  V8 {sid}: chart[{idx}] '{entry.get('kind')}' "
            f"@{ts:.2f}s dur={dur:.2f}s → {mov_path.name}"
        )

    return placed
