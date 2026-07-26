"""SFX-хореография: под КАЖДУЮ анимацию — фиттинговые звуки по её битам,
сопровождая до конца. Громкость выровнена (loudnorm). Кладёт на A5 (длинные:
разгон/ревилер) и A6 (точечные: тик/удар/вуш), чтобы не затирать друг друга.

Типы→звуки:
  shock   : разгон весь климб (0) + удар на приземлении (3.07с)
  crowd   : разгон на заливку (0.4) + удар когда заполнилось (2.47с)
  timeline: вуш на старт + тик на КАЖДОЕ событие (камера доезжает)
  network : тик на КАЖДЫЙ узел (nodeStart)
  kinetic : вуш (слова влетают)
  mapspread: ревилер (пятно растекается)
  cine/dossier: вуш на появление
  name/stat/evidence/…: тик
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pymiere
from pymiere.wrappers import time_from_seconds
from services.premiere_template.timeline_ops import import_media

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-"
SFX = (PROJECT / "assets" / "sfx").resolve()
LONG_TRACK = 4   # A5 — длинные (разгон/ревилер)
PT_TRACK = 5     # A6 — точечные (тик/удар/вуш)
LONG = {"riser", "reveal"}


def beats(o):
    t = o.get("type", "")
    p = o.get("props", {}) or {}
    s = float(o["start"])
    cid = o.get("id", "")
    out = []
    if t == "shock":
        out = [(s, "riser"), (s + 3.07, "impact")]
    elif t == "crowd":
        out = [(s + 0.4, "riser"), (s + 2.47, "impact")]
    elif t == "timeline":
        ev = p.get("events", []); n = max(1, len(ev))
        dur = p.get("durationInFrames") or max(120, 50 + n * 55)
        span = max(1.0, dur - 64)
        out = [(s, "appear")]
        for i in range(n):
            out.append((s + (26 + span * (i / max(1, n - 1))) / 30.0, "tick"))
    elif t == "network":
        ns = p.get("nodeStart") or [8 + i * 7 for i in range(len(p.get("nodes", [])))]
        out = [(s + f / 30.0, "tick") for f in ns]
    elif t == "kinetic":
        out = [(s, "swoosh")]
    elif t == "mapspread":
        out = [(s, "reveal")]
    elif t == "cine" or cid.startswith("cine") or cid.startswith("dos") or cid.startswith("arch_0") or t == "dossier":
        out = [(s, "appear")]
    else:  # name/stat/evidence/compare/percent/ratio/phrase/spotlight/map/quote
        out = [(s, "tick")]
    return out


def main() -> int:
    ov = json.loads((PROJECT / "overlays_rendered.json").read_text(encoding="utf-8"))["overlays"]
    cine = json.loads((PROJECT / "cine_scenes.json").read_text(encoding="utf-8"))["scenes"]
    for c in cine:
        c.setdefault("type", "cine")
    graphics = ov + cine

    seq = pymiere.objects.app.project.activeSequence
    a5 = seq.audioTracks[LONG_TRACK]
    a6 = seq.audioTracks[PT_TRACK]
    for tr in (a5, a6):
        for cl in reversed(list(tr.clips)):
            cl.remove(False, False)

    items = {}
    for k in ("appear", "riser", "impact", "tick", "reveal", "swoosh", "notify"):
        items[k] = import_media(SFX / f"sfx2_{k}.wav")

    placed = 0
    for g in graphics:
        for (t, sfx) in beats(g):
            item = items.get(sfx)
            if item is None or t < 0:
                continue
            tr = a5 if sfx in LONG else a6
            try:
                tr.overwriteClip(item, time_from_seconds(round(t, 2)))
                placed += 1
            except Exception:
                pass
    pymiere.objects.app.project.save()
    print(f"SFX-битов расставлено: {placed} (графиков {len(graphics)}) на A5/A6")
    return 0


if __name__ == "__main__":
    sys.exit(main())
