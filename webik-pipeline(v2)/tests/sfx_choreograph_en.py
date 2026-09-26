"""SFX-хореография DreamWorks: по типам приёмов графики (graphics_plan_v2_dw.json) + киновставкам (V8).
Пулы assets/sfx: w* вуши, t* тики, i* удары, r* ревилеры. БЕЗ восходящих ризеров.
Ставит по битам на A5 (длинные ревилеры) / A6 (точечные тики/удары/вуши). Ротация без повторов."""
import glob, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pymiere
from pymiere.wrappers import time_from_seconds
from services.premiere_template.timeline_ops import import_media

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-08-25_aysberg-dreamworks-lost-media-i-temnaya-skrytaya-storona-stu_EN"
SFX = (PROJECT / "assets" / "sfx").resolve()
LONG_TRACK = 4   # A5 — ревилеры
PT_TRACK = 5     # A6 — точечные
TRAGEDY_DROP = {"scene_092", "scene_141", "scene_214"}


def pool(prefix):
    return sorted(Path(p) for p in glob.glob(str(SFX / f"{prefix}[0-9]*.wav")))


def gbeats(t, s, dur, v):
    """биты по типу приёма: список (время, категория)"""
    if t in ("dossier", "cut_stamp", "terminated"):
        return [(s, "reveal"), (s + 1.0, "impact")]
    if t == "headline":
        return [(s, "whoosh"), (s + 0.9, "impact")]
    if t == "money":
        return [(s + 0.3, "tick"), (s + 0.8, "tick"), (s + 1.3, "tick"), (s + 1.8, "tick"), (s + 2.15, "impact")]
    if t == "timeline":
        ev = (v.get("events") or []); n = max(1, len(ev)); span = max(1.0, dur - 1.2)
        return [(s + 0.4 + span * (i / max(1, n - 1)), "tick") for i in range(n)]
    if t == "glitch":
        return [(s, "impact"), (s + 0.4, "tick"), (s + 0.8, "tick")]
    if t == "drama_freeze":
        return [(s, "impact")]
    if t in ("filmstrip", "split", "uncanny"):
        return [(s, "whoosh")]
    if t == "quote":
        return [(s, "tick")]
    return [(s, "whoosh")]


def main() -> int:
    pools = {"whoosh": pool("w"), "tick": pool("t"), "impact": pool("i"), "reveal": pool("r")}
    for k, val in pools.items():
        print(f"  пул {k}: {len(val)}")
        if not val: print("  ПУСТО"); return 1

    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    plan = json.loads((PROJECT / "graphics_plan_v2_dw.json").read_text(encoding="utf-8"))
    # применяем те же переназначения, что в раскатке (влияет на биты)
    for sid, t in {"scene_196": "glitch", "scene_211": "drama_freeze"}.items():
        if sid in plan: plan[sid]["treatment"] = t

    events = []  # (time, cat)
    for sid, v in plan.items():
        if sid not in al: continue
        s = al[sid]["start"]; dur = max(2.0, al[sid]["end"] - al[sid]["start"]) + 0.3
        events += gbeats(v.get("treatment"), s, dur, v)

    # киновставки на V8 → вуш (только реально уложенные: минус трагедия, минус занятые графикой)
    cutp = PROJECT / "cutaways_dw.json"
    if cutp.exists():
        for r in json.loads(cutp.read_text(encoding="utf-8")):
            sid = r.get("id")
            if sid in al and sid not in TRAGEDY_DROP and sid not in plan:
                events.append((al[sid]["start"], "whoosh"))

    events.sort()
    seq = pymiere.objects.app.project.activeSequence
    a5, a6 = seq.audioTracks[LONG_TRACK], seq.audioTracks[PT_TRACK]
    for tr in (a5, a6):
        for cl in reversed(list(tr.clips)): cl.remove(False, False)

    items, counters = {}, {k: 0 for k in pools}
    def get_item(p):
        if p not in items: items[p] = import_media(p)
        return items[p]
    def pick(cat):
        val = pools[cat]; i = counters[cat] % len(val); counters[cat] += 1; return val[i]

    placed = 0
    for (tm, cat) in events:
        if tm < 0: continue
        it = get_item(pick(cat))
        if it is None: continue
        tr = a5 if cat == "reveal" else a6
        try: tr.overwriteClip(it, time_from_seconds(round(tm, 2))); placed += 1
        except Exception: pass
    before = (PROJECT / "project_template.prproj").stat().st_mtime
    pymiere.objects.app.project.save()
    import time; time.sleep(1.5)
    ok = "OK" if (PROJECT / "project_template.prproj").stat().st_mtime > before else "NO"
    print(f"SFX-битов: {placed} (событий {len(events)}) | A5=ревилеры A6=точечные | save {ok}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
