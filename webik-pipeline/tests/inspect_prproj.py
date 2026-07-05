"""
inspect_prproj.py
Открывает указанный .prproj файл в Premiere через Pymiere и дампит:
  - параметры sequence (resolution/fps)
  - per-track per-clip components и их properties
  - спец-внимание на Graphics/Text components (MGT, Title)

Output:
  - JSON отчёт в projects/_inspections/<prproj-stem>__<timestamp>.json
  - Console pretty-print

Использование:
  & .venv\\Scripts\\python.exe tests\\inspect_prproj.py "C:\\path\\to\\file.prproj"

Премиер должен быть открыт (и ничего важного не открыто — мы откроем твой проект,
read-only, но Premiere всё равно покажет его. После инспекции просто закрой проект
без сохранения).
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pymiere
from pymiere import exe_utils

from core.logger import setup_logger

log = setup_logger("inspect_prproj")


def _safe(call, default=None):
    try:
        return call()
    except Exception:
        return default


def _dump_property(prop) -> dict:
    out = {
        "displayName": _safe(lambda: prop.displayName),
    }
    val = _safe(lambda: prop.getValue())
    if val is not None:
        try:
            json.dumps(val)
            out["value"] = val
        except Exception:
            out["value_repr"] = repr(val)[:200]
    # Streams (keyframed)
    streams = _safe(lambda: prop.getKeyframeListAsString()) if hasattr(prop, "getKeyframeListAsString") else None
    if streams:
        out["keyframes_str"] = streams[:300]
    return out


def _dump_component(comp, comp_idx: int) -> dict:
    out = {
        "idx": comp_idx,
        "displayName": _safe(lambda: comp.displayName),
        "matchName": _safe(lambda: comp.matchName),
        "properties": [],
    }
    n_props = _safe(lambda: comp.properties.numItems, 0) or 0
    for k in range(n_props):
        p = _safe(lambda: comp.properties[k])
        if p is None:
            continue
        out["properties"].append(_dump_property(p))
    return out


def _dump_clip(clip, clip_idx: int) -> dict:
    name = _safe(lambda: clip.name)
    out = {
        "idx": clip_idx,
        "name": name,
        "type": _safe(lambda: clip.mediaType),
        "start": _safe(lambda: clip.start.seconds),
        "end": _safe(lambda: clip.end.seconds),
        "duration": _safe(lambda: clip.duration.seconds),
        "components": [],
    }
    n_comps = _safe(lambda: clip.components.numItems, 0) or 0
    for c in range(n_comps):
        comp = _safe(lambda: clip.components[c])
        if comp is None:
            continue
        out["components"].append(_dump_component(comp, c))
    return out


def _dump_track(track, track_idx: int, kind: str) -> dict:
    n_clips = _safe(lambda: track.clips.numItems, 0) or 0
    out = {
        "kind": kind,
        "idx": track_idx,
        "name": _safe(lambda: track.name) or f"{kind}{track_idx + 1}",
        "n_clips": n_clips,
        "clips": [],
    }
    for j in range(n_clips):
        clip = _safe(lambda: track.clips[j])
        if clip is None:
            continue
        out["clips"].append(_dump_clip(clip, j))
    return out


def _dump_sequence(seq, seq_idx: int) -> dict:
    settings = _safe(lambda: seq.getSettings())
    out = {
        "idx": seq_idx,
        "name": _safe(lambda: seq.name),
        "video_w": _safe(lambda: settings.videoFrameWidth) if settings else None,
        "video_h": _safe(lambda: settings.videoFrameHeight) if settings else None,
        "duration_sec": _safe(lambda: seq.end.seconds),
        "video_tracks": [],
        "audio_tracks": [],
    }
    n_v = _safe(lambda: seq.videoTracks.numTracks, 0) or 0
    for i in range(n_v):
        vt = _safe(lambda: seq.videoTracks[i])
        if vt is None:
            continue
        out["video_tracks"].append(_dump_track(vt, i, "V"))
    n_a = _safe(lambda: seq.audioTracks.numTracks, 0) or 0
    for i in range(n_a):
        at = _safe(lambda: seq.audioTracks[i])
        if at is None:
            continue
        out["audio_tracks"].append(_dump_track(at, i, "A"))
    return out


def inspect(prproj_path: Path, skip_open: bool = False) -> dict:
    if not exe_utils.is_premiere_running():
        raise RuntimeError(
            "Premiere не запущен. Открой Premiere (любой проект), потом запусти этот скрипт снова."
        )

    log.info(f"Premiere version: {pymiere.objects.app.version}")

    if skip_open:
        log.info("Использую УЖЕ открытый в Premiere проект (skip_open=True)")
        project = pymiere.objects.app.project
        if project is None:
            raise RuntimeError("Нет открытого проекта в Premiere — открой его руками и повтори.")
        log.info(f"Активный проект: {project.name}")
    else:
        log.info(f"Открываю проект: {prproj_path}")
        if not prproj_path.exists():
            raise FileNotFoundError(prproj_path)
        pymiere.objects.app.openDocument(str(prproj_path))
        time.sleep(2.0)  # дать Premiere время прочитать
        project = pymiere.objects.app.project

    n_seq = _safe(lambda: project.sequences.numSequences, 0) or 0
    log.info(f"В проекте {n_seq} sequence(s)")
    out = {
        "premiere_version": pymiere.objects.app.version,
        "prproj": str(prproj_path),
        "inspected_at": datetime.now().isoformat(),
        "sequences": [],
    }
    for i in range(n_seq):
        seq = _safe(lambda: project.sequences[i])
        if seq is None:
            continue
        log.info(f"  → sequence[{i}]: {_safe(lambda: seq.name)}")
        out["sequences"].append(_dump_sequence(seq, i))

    return out


def find_text_components(report: dict):
    """Печатает только то, что похоже на Text/Graphics компоненты."""
    print("\n========== TEXT/GRAPHICS COMPONENTS ==========")
    for seq in report["sequences"]:
        print(f"\n--- Sequence: {seq['name']} ({seq['video_w']}x{seq['video_h']}) ---")
        for vt in seq["video_tracks"]:
            for clip in vt["clips"]:
                for comp in clip["components"]:
                    dn = (comp.get("displayName") or "").lower()
                    mn = (comp.get("matchName") or "").lower()
                    is_text = any(kw in (dn + " " + mn) for kw in [
                        "text", "title", "graphic", "mogrt", "type"
                    ])
                    if not is_text:
                        continue
                    print(
                        f"  [{vt['name']}] clip='{clip['name']}' "
                        f"@{clip['start']:.2f}-{clip['end']:.2f}s "
                        f"comp={comp['displayName']} (match={comp['matchName']})"
                    )
                    for p in comp["properties"]:
                        v = p.get("value", p.get("value_repr", ""))
                        if v in ("", None):
                            continue
                        sv = str(v)
                        if len(sv) > 80:
                            sv = sv[:80] + "..."
                        print(f"      • {p['displayName']}: {sv}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: inspect_prproj.py <path-to-prproj> [--skip-open]")
        sys.exit(2)

    prproj = Path(sys.argv[1])
    skip_open = "--skip-open" in sys.argv[2:]
    out_dir = ROOT / "projects" / "_inspections"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{prproj.stem}__{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    report = inspect(prproj, skip_open=skip_open)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info(f"Полный JSON отчёт: {out_path}")

    find_text_components(report)
    print(f"\n[DONE] full report saved to: {out_path}")
