"""
services/observability/timeline_reporter.py
Post-Stage-5 отчёт по таймлайну: что и куда легло, какие пробелы.

Решает жалобу: «непонятно где клип уходит, где срезается».

Генерит два файла в project_dir:
- timeline_manifest.json — машиночитаемый снимок всех треков и клипов
- timeline_preview.html  — визуальная горизонтальная диаграмма (пустой браузер
                           откроет без сервера, без зависимостей)

Источник данных — pymiere.Sequence (после build_rough_cut). Если pymiere что-то
не отдаёт по конкретному клипу — записываем error в clip-entry, не падаем.
"""
from __future__ import annotations

import json
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.logger import setup_logger

log = setup_logger("timeline-report")

GAP_WARN_SEC = 0.05  # игнорируем щели меньше 50ms (frame-level rounding)
SHORT_CLIP_WARN_SEC = 0.5  # подозрительно короткий клип

# Простая палитра для треков (повторяется по модулю)
TRACK_COLORS = [
    "#3b82f6", "#ef4444", "#22c55e", "#eab308", "#a855f7",
    "#06b6d4", "#f97316", "#ec4899", "#14b8a6", "#f43f5e",
]


def _safe(fn, default=None):
    """Tolerant getattr для pymiere — некоторые свойства бросают на пустых треках."""
    try:
        return fn()
    except Exception:
        return default


def _read_clip(clip, track_label: str, clip_idx: int) -> Dict[str, Any]:
    """Извлекает что-то полезное из pymiere TrackItem. Tolerant к ошибкам."""
    entry: Dict[str, Any] = {"index": clip_idx}
    try:
        start = clip.start.seconds
        end = clip.end.seconds
        entry["start"] = round(start, 3)
        entry["end"] = round(end, 3)
        entry["duration"] = round(end - start, 3)
    except Exception as e:
        entry["error"] = f"timing read failed: {e}"
        return entry

    entry["name"] = _safe(lambda: clip.name) or "?"
    project_item = _safe(lambda: clip.projectItem)
    if project_item is not None:
        entry["source"] = _safe(lambda: project_item.name) or entry["name"]
        path = _safe(lambda: project_item.getMediaPath())
        if path:
            entry["media_path"] = path
    return entry


def _read_track(track, track_label: str) -> Dict[str, Any]:
    """Возвращает {name, clips: [...]} для одного pymiere track'а."""
    clips_data: List[Dict[str, Any]] = []
    n_items = _safe(lambda: track.clips.numItems, default=0) or 0
    for i in range(n_items):
        try:
            clip = track.clips[i]
        except Exception as e:
            clips_data.append({"index": i, "error": f"clip read failed: {e}"})
            continue
        clips_data.append(_read_clip(clip, track_label, i))

    return {
        "name": _safe(lambda: track.name) or track_label,
        "clip_count": len(clips_data),
        "clips": clips_data,
    }


def _coverage_during(tracks: Dict[str, Dict[str, Any]], from_t: float, to_t: float,
                     exclude: str) -> List[Dict[str, str]]:
    """Возвращает список клипов с других треков, перекрывающих [from_t, to_t]."""
    covering = []
    for label, track in tracks.items():
        if label == exclude:
            continue
        for c in track["clips"]:
            if "start" not in c or "end" not in c:
                continue
            # Любое пересечение [c.start, c.end] с [from_t, to_t]
            if c["end"] > from_t and c["start"] < to_t:
                covering.append({"track": label, "name": c.get("name") or "?"})
    return covering


def _detect_warnings(tracks: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Детектит проблемы: пробелы на V1 (с annotation покрытия), короткие клипы."""
    warnings: List[Dict[str, Any]] = []

    # Gaps на V1 (главный визуальный трек) — между концом одного клипа и началом следующего
    v1 = tracks.get("V1")
    if v1:
        clips = sorted(
            (c for c in v1["clips"] if "start" in c and "end" in c),
            key=lambda c: c["start"],
        )
        for prev, curr in zip(clips, clips[1:]):
            gap = curr["start"] - prev["end"]
            if gap > GAP_WARN_SEC:
                covered_by = _coverage_during(tracks, prev["end"], curr["start"], exclude="V1")
                # Если gap полностью покрыт хотя бы одним клипом другого V-трека — не считаем дырой
                fully_covered = any(
                    c["track"].startswith("V") and _is_fully_covered(
                        tracks[c["track"]]["clips"], prev["end"], curr["start"]
                    )
                    for c in covered_by
                )
                warnings.append({
                    "track": "V1",
                    "issue": "gap_covered" if fully_covered else "gap",
                    "from": prev["end"],
                    "to": curr["start"],
                    "duration": round(gap, 3),
                    "after_clip": prev.get("name"),
                    "before_clip": curr.get("name"),
                    "covered_by": covered_by,
                })

    # Подозрительно короткие клипы (везде)
    for track_label, track in tracks.items():
        for c in track["clips"]:
            dur = c.get("duration")
            if dur is not None and 0 < dur < SHORT_CLIP_WARN_SEC:
                warnings.append({
                    "track": track_label,
                    "issue": "short_clip",
                    "duration": dur,
                    "name": c.get("name"),
                    "start": c.get("start"),
                })

    return warnings


def _is_fully_covered(clips: List[Dict[str, Any]], from_t: float, to_t: float) -> bool:
    """Проверяет что хотя бы один клип в `clips` целиком покрывает [from_t, to_t]."""
    for c in clips:
        if "start" not in c or "end" not in c:
            continue
        if c["start"] <= from_t + GAP_WARN_SEC and c["end"] >= to_t - GAP_WARN_SEC:
            return True
    return False


def collect_manifest(sequence) -> Dict[str, Any]:
    """Читает pymiere Sequence в plain dict."""
    tracks: Dict[str, Dict[str, Any]] = {}

    # Video tracks: V1..VN
    n_video = _safe(lambda: sequence.videoTracks.numTracks, default=0) or 0
    for i in range(n_video):
        try:
            t = sequence.videoTracks[i]
        except Exception as e:
            tracks[f"V{i+1}"] = {"name": "?", "clip_count": 0, "clips": [], "error": str(e)}
            continue
        tracks[f"V{i+1}"] = _read_track(t, f"V{i+1}")

    # Audio tracks: A1..AN
    n_audio = _safe(lambda: sequence.audioTracks.numTracks, default=0) or 0
    for i in range(n_audio):
        try:
            t = sequence.audioTracks[i]
        except Exception as e:
            tracks[f"A{i+1}"] = {"name": "?", "clip_count": 0, "clips": [], "error": str(e)}
            continue
        tracks[f"A{i+1}"] = _read_track(t, f"A{i+1}")

    # Total duration: max по всем V-трекам — захватываем outro (V10) который
    # extends за V1. Audio-треки игнорим: Premiere иногда даёт inflated clip.end
    # для re-imported mp3 (cached metadata quirk).
    total = 0.0
    for label, t in tracks.items():
        if not label.startswith("V"):
            continue
        for c in t["clips"]:
            if "end" in c:
                total = max(total, c["end"])
    if total <= 0:
        # Финальный fallback — берём из всех клипов
        for t in tracks.values():
            for c in t["clips"]:
                if "end" in c:
                    total = max(total, c["end"])

    warnings = _detect_warnings(tracks)

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "sequence_name": _safe(lambda: sequence.name) or "?",
        "total_duration_sec": round(total, 3),
        "tracks": tracks,
        "warnings": warnings,
    }


def _render_html(manifest: Dict[str, Any]) -> str:
    """Минимальный self-contained HTML с горизонтальными цветными барами."""
    total = max(manifest["total_duration_sec"], 0.1)
    track_names = list(manifest["tracks"].keys())
    # Сортируем: V1..VN сверху, потом A1..AN снизу (привычный layout таймлайна)
    video_tracks = sorted([t for t in track_names if t.startswith("V")],
                          key=lambda x: int(x[1:]))
    audio_tracks = sorted([t for t in track_names if t.startswith("A")],
                          key=lambda x: int(x[1:]))
    ordered = video_tracks + audio_tracks

    rows_html = []
    for i, label in enumerate(ordered):
        track = manifest["tracks"][label]
        color = TRACK_COLORS[i % len(TRACK_COLORS)]
        clip_blocks = []
        for c in track["clips"]:
            if "start" not in c or "end" not in c:
                continue
            left_pct = 100.0 * c["start"] / total
            width_pct = 100.0 * (c["end"] - c["start"]) / total
            label_text = c.get("name") or c.get("source") or "?"
            tooltip = (
                f"{label}: {label_text}\n"
                f"start={c['start']:.2f}s  end={c['end']:.2f}s  dur={c.get('duration', 0):.2f}s"
            )
            clip_blocks.append(
                f'<div class="clip" style="left:{left_pct:.3f}%; '
                f'width:{width_pct:.3f}%; background:{color};" '
                f'title="{escape(tooltip)}">'
                f'<span class="cliplabel">{escape(label_text[:40])}</span>'
                f'</div>'
            )
        rows_html.append(
            f'<div class="row"><div class="rowlabel">{escape(label)} '
            f'<span class="ct">×{track["clip_count"]}</span></div>'
            f'<div class="lane">{"".join(clip_blocks)}</div></div>'
        )

    real_warns = [w for w in manifest["warnings"] if w["issue"] != "gap_covered"]
    info_warns = [w for w in manifest["warnings"] if w["issue"] == "gap_covered"]

    def _fmt_warn(w):
        if w["issue"] in ("gap", "gap_covered"):
            cover = ""
            if w.get("covered_by"):
                names = ", ".join(
                    f"{c['track']}:{escape(str(c['name'])[:30])}" for c in w["covered_by"]
                )
                cover = f' [covered by {names}]'
            return (
                f'<b>{w["track"]}</b> gap {w["duration"]:.2f}s '
                f'@ {w["from"]:.2f}s → {w["to"]:.2f}s '
                f'(между «{escape(str(w.get("after_clip") or "?"))}» '
                f'и «{escape(str(w.get("before_clip") or "?"))}»){cover}'
            )
        if w["issue"] == "short_clip":
            return (
                f'<b>{w["track"]}</b> short clip {w["duration"]:.2f}s '
                f'@ {w["start"]:.2f}s — «{escape(str(w.get("name") or "?"))}»'
            )
        return escape(json.dumps(w, ensure_ascii=False))

    warns_html = ""
    if real_warns:
        items = "".join(f"<li>{_fmt_warn(w)}</li>" for w in real_warns)
        warns_html += f'<div class="warns"><h3>Warnings ({len(real_warns)})</h3><ul>{items}</ul></div>'
    if info_warns:
        items = "".join(f"<li>{_fmt_warn(w)}</li>" for w in info_warns)
        warns_html += f'<div class="infos"><h3>Info ({len(info_warns)}) — closed gaps</h3><ul>{items}</ul></div>'

    # Time-axis ticks каждые 5 секунд
    ticks_html = []
    t = 0
    while t <= total:
        left_pct = 100.0 * t / total
        ticks_html.append(
            f'<div class="tick" style="left:{left_pct:.3f}%;">'
            f'<span class="ticklbl">{t}s</span></div>'
        )
        t += 5

    return f"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<title>Timeline preview — {escape(manifest["sequence_name"])}</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, sans-serif; margin: 0; padding: 16px; background: #0f1115; color: #e5e7eb; }}
  h1 {{ font-size: 18px; margin: 0 0 8px; }}
  .meta {{ color: #9ca3af; font-size: 12px; margin-bottom: 16px; }}
  .timeline {{ background: #1a1d23; border-radius: 6px; padding: 12px 12px 24px; position: relative; }}
  .row {{ display: flex; align-items: center; margin-bottom: 4px; }}
  .rowlabel {{ width: 48px; font-weight: 700; font-size: 13px; color: #d1d5db; flex-shrink: 0; }}
  .ct {{ font-weight: 400; color: #6b7280; font-size: 11px; }}
  .lane {{ position: relative; flex: 1; height: 24px; background: #14171c; border-radius: 3px; overflow: hidden; }}
  .clip {{ position: absolute; top: 0; bottom: 0; opacity: 0.85; border-right: 1px solid rgba(0,0,0,0.5); display: flex; align-items: center; padding: 0 4px; cursor: default; }}
  .clip:hover {{ opacity: 1.0; }}
  .cliplabel {{ font-size: 10px; color: #fff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-shadow: 0 1px 1px rgba(0,0,0,0.6); }}
  .ticks {{ position: relative; height: 18px; margin-top: 8px; margin-left: 48px; }}
  .tick {{ position: absolute; top: 0; height: 6px; border-left: 1px solid #374151; }}
  .ticklbl {{ position: absolute; top: 6px; left: -12px; font-size: 10px; color: #6b7280; }}
  .warns {{ margin-top: 16px; padding: 12px; background: #2a1a1a; border-left: 3px solid #ef4444; border-radius: 4px; }}
  .warns h3 {{ margin: 0 0 8px; font-size: 14px; color: #fca5a5; }}
  .warns ul {{ margin: 0; padding-left: 20px; font-size: 12px; }}
  .warns li {{ margin-bottom: 4px; }}
  .infos {{ margin-top: 12px; padding: 12px; background: #1a2233; border-left: 3px solid #3b82f6; border-radius: 4px; }}
  .infos h3 {{ margin: 0 0 8px; font-size: 14px; color: #93c5fd; }}
  .infos ul {{ margin: 0; padding-left: 20px; font-size: 12px; color: #cbd5e1; }}
  .infos li {{ margin-bottom: 4px; }}
</style>
</head><body>
<h1>{escape(manifest["sequence_name"])}</h1>
<div class="meta">
  generated {escape(manifest["generated_at"])} · total {manifest["total_duration_sec"]:.2f}s ·
  {len(ordered)} tracks · {sum(t["clip_count"] for t in manifest["tracks"].values())} clips
</div>
<div class="timeline">
  {"".join(rows_html)}
  <div class="ticks">{"".join(ticks_html)}</div>
</div>
{warns_html}
</body></html>"""


def write_report(sequence, project_dir: Path) -> Dict[str, Path]:
    """Главная точка входа. Пишет manifest.json + preview.html, возвращает пути."""
    manifest = collect_manifest(sequence)

    json_path = project_dir / "timeline_manifest.json"
    html_path = project_dir / "timeline_preview.html"

    json_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    html_path.write_text(_render_html(manifest), encoding="utf-8")

    n_clips = sum(t["clip_count"] for t in manifest["tracks"].values())
    n_warns = len(manifest["warnings"])
    log.info(
        f"Timeline report: {len(manifest['tracks'])} tracks, "
        f"{n_clips} clips, {n_warns} warnings → {json_path.name} + {html_path.name}"
    )
    return {"json": json_path, "html": html_path}
