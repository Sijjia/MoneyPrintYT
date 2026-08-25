"""SFX-хореография (КНДР): пул вариантов на категорию + ротация, звуки не повторяются.
БЕЗ восходящего swoosh/riser. Пулы assets/sfx/: w* вуши, t* тики, i* удары, r* ревилеры.
Ставит по битам анимаций (overlays_rendered.json + cine_scenes.json) на A5(длинные)/A6(точечные)."""
import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pymiere
from pymiere.wrappers import time_from_seconds
from services.premiere_template.timeline_ops import import_media

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-08-18_aysberg-evolyutsii-temnaya-i-zapretnaya-storona-evolyutsii-o"
SFX = (PROJECT / "assets" / "sfx").resolve()
LONG_TRACK = 4   # A5 — длинные (ревилеры)
PT_TRACK = 5     # A6 — точечные (тики/удары/вуши)


def pool(prefix):
    return sorted(Path(p) for p in glob.glob(str(SFX / f"{prefix}[0-9]*.wav")))


def crowd_ticks(s, climb_end):
    ts = []
    for frac in (0.15, 0.45, 0.72, 0.9):
        ts.append((s + climb_end * frac, "tick"))
    ts.append((s + climb_end, "impact"))
    return ts


def beats(o):
    t = o.get("type", "")
    p = o.get("props", {}) or {}
    s = float(o["start"])
    cid = o.get("id", "")
    if t == "shock":
        return crowd_ticks(s, 3.07)
    if t == "crowd":
        return crowd_ticks(s, 2.47)
    if t == "timeline":
        ev = p.get("events", []); n = max(1, len(ev))
        dur = p.get("durationInFrames") or max(120, 50 + n * 55)
        span = max(1.0, dur - 64)
        return [(s + (26 + span * (i / max(1, n - 1))) / 30.0, "tick") for i in range(n)]
    if t == "network":
        ns = p.get("nodeStart") or [8 + i * 7 for i in range(len(p.get("nodes", [])))]
        return [(s + f / 30.0, "tick") for f in ns]
    if t == "kinetic":
        return [(s, "whoosh")]
    if t == "mapspread":
        return [(s, "reveal")]
    if t == "cine" or cid.startswith("cine") or cid.startswith("dos") or cid.startswith("arch_0") or t == "dossier":
        return [(s, "whoosh")]
    return [(s, "tick")]


def main() -> int:
    pools = {"whoosh": pool("w"), "tick": pool("t"), "impact": pool("i"), "reveal": pool("r")}
    for k, v in pools.items():
        print(f"  пул {k}: {len(v)} вариантов")
        if not v:
            print("  ПУСТО — скачай звуки"); return 1

    ov = json.loads((PROJECT / "overlays_rendered.json").read_text(encoding="utf-8"))["overlays"]
    cine = json.loads((PROJECT / "cine_scenes.json").read_text(encoding="utf-8"))["scenes"]
    for c in cine:
        c.setdefault("type", "cine")
    graphics = sorted(ov + cine, key=lambda g: g["start"])

    seq = pymiere.objects.app.project.activeSequence
    a5, a6 = seq.audioTracks[LONG_TRACK], seq.audioTracks[PT_TRACK]
    for tr in (a5, a6):
        for cl in reversed(list(tr.clips)):
            cl.remove(False, False)

    items = {}
    def get_item(pth):
        if pth not in items:
            items[pth] = import_media(pth)
        return items[pth]

    counters = {k: (sum(ord(c) for c in "seed") % max(1, len(v))) for k, v in pools.items()}

    def pick(cat):
        v = pools[cat]
        i = counters[cat] % len(v)
        counters[cat] += 1
        return v[i]

    placed = 0
    for g in graphics:
        for (t, cat) in beats(g):
            if t < 0:
                continue
            item = get_item(pick(cat))
            if item is None:
                continue
            tr = a5 if cat == "reveal" else a6
            try:
                tr.overwriteClip(item, time_from_seconds(round(t, 2)))
                placed += 1
            except Exception:
                pass
    pymiere.objects.app.project.save()
    print(f"SFX-битов расставлено: {placed} (графиков {len(graphics)}), варианты ротируются")
    return 0


if __name__ == "__main__":
    sys.exit(main())
