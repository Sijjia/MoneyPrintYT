"""Переукладка графики на V8 по НОВЫМ позициям (после переякоривания).
Использует import_media (находит уже импортированные item'ы), не плодит импорты.
Чистит V8, кладёт кино-сцены + оверлеи с дедупом (сцена поглощает оверлеи в окне).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pymiere
from pymiere.wrappers import time_from_seconds
from services.premiere.effects import find_clip_by_timeline_start, mute_linked_audio
from services.premiere_template.timeline_ops import import_media

PROJECT = Path("projects/2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-")
PROJ_ABS = PROJECT.resolve()
V8 = 7


def resolve_cine(cid: str) -> Path | None:
    for d in ("dossier", "arche2", "arche", "cine4", "cine3", "cine2", "cine", "arche3", "arche3b"):
        p = PROJ_ABS / "assets" / d / f"{cid}.mov"
        if p.exists():
            return p
    return None


def resolve_overlay(o: dict) -> Path | None:
    raw = Path(o.get("file", ""))
    for c in ([raw] if raw.is_absolute() else [Path.cwd() / raw, PROJ_ABS / raw]):
        if c.exists():
            return c.resolve()
    return None


def main() -> int:
    cine = json.loads((PROJECT / "cine_scenes.json").read_text(encoding="utf-8"))["scenes"]
    quick = json.loads((PROJECT / "overlays_rendered.json").read_text(encoding="utf-8"))["overlays"]
    for c in cine:
        c["file"] = str(resolve_cine(c["id"]) or "")
    spans = [(c["start"], c["start"] + c["duration_sec"]) for c in cine if c["file"]]
    quick2 = [q for q in quick if not any(s <= q["start"] < e for s, e in spans)]
    absorbed = len(quick) - len(quick2)
    allg = [g for g in (quick2 + cine) if (g.get("file"))]
    allg.sort(key=lambda g: g["start"])

    seq = pymiere.objects.app.project.activeSequence
    v = seq.videoTracks[V8]
    for cl in reversed(list(v.clips)):
        cl.remove(False, False)
    print(f"V8 очищен | кино {len(cine)} | быстрых поглощено {absorbed} | к укладке {len(allg)}")

    placed = 0
    for g in allg:
        f = Path(g["file"])
        if not f.exists():
            print(f"  нет файла {g['id']}"); continue
        item = import_media(f)
        if item is None:
            print(f"  не импортировался {g['id']}"); continue
        try:
            v.overwriteClip(item, time_from_seconds(float(g["start"])))
        except Exception as e:
            print(f"  {g['id']} @{g['start']}: overwrite упал {e}"); continue
        clip = find_clip_by_timeline_start(v, float(g["start"]))
        if clip is not None:
            try:
                mute_linked_audio(clip)
            except Exception:
                pass
        placed += 1
    pymiere.objects.app.project.save()
    print(f"уложено {placed}/{len(allg)}, сохранено")
    return 0


if __name__ == "__main__":
    sys.exit(main())
