"""SFX-хореография GTA: биты по ОВЕРЛЕЯМ (overlays_rendered.json) + bespoke-открывашкам
(records/bigfoot/ufo/kurtaj) + маскот-врезки. БЕЗ звуков под карточками уровней (Айдар).
Пулы assets/sfx: w вуши, t тики, i удары, r ревилеры. A5(idx4)=ревилеры, A6(idx5)=точечные, тихо.
  ../webik-pipeline/.venv/Scripts/python.exe tests/sfx_choreograph_gta.py"""
import glob, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
from pymiere.wrappers import time_from_seconds
from services.premiere_template.timeline_ops import import_media
from tests.assemble_iceberg_test import set_clip_volume

PROJECT = ROOT / "projects" / "2026-09-06_aysberg-gta-temnaya-storona-realnye-dela-vnutriigrovye-tayny"
SFX = (PROJECT / "assets" / "sfx").resolve()
LONG_TRACK = 4   # A5 — ревилеры
PT_TRACK = 5     # A6 — точечные
SFX_VOL = 0.5
# bespoke-открывашки (маскот+графика) — тут яркий заход whoosh+impact
BESPOKE_STARTS = ["scene_008", "scene_013", "scene_062", "scene_160"]
# маскот-врезки
MASCOT_SCENES = ["scene_085"]


def pool(prefix):
    return sorted(Path(p) for p in glob.glob(str(SFX / f"{prefix}[0-9]*.wav")))


def overlay_beats(otype, s):
    if otype in ("stat", "percent", "ratio"):
        return [(s + 0.15, "impact")]
    if otype == "timeline":
        return [(s + 0.4, "tick"), (s + 1.1, "tick"), (s + 1.8, "tick")]
    if otype == "compare":
        return [(s, "whoosh"), (s + 0.7, "impact")]
    if otype == "quote":
        return [(s, "tick")]
    return [(s, "whoosh")]  # name/phrase/прочее


def main() -> int:
    pools = {"whoosh": pool("w"), "tick": pool("t"), "impact": pool("i"), "reveal": pool("r")}
    for k, val in pools.items():
        print(f"  пул {k}: {len(val)}")
        if not val:
            print("  ПУСТО — скопируй пул в assets/sfx"); return 1

    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    sc = {s["id"]: s for s in json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]}
    overlays = json.loads((PROJECT / "overlays_rendered.json").read_text(encoding="utf-8"))["overlays"]
    # сцены-уровни — НЕ трогаем
    level_ids = {sid for sid, s in sc.items() if (s.get("visual") or {}).get("type") == "level_card"}

    events = []
    # 1) оверлеи (по текущему alignment сцены, кроме уровней)
    for ov in overlays:
        sid = ov.get("scene_id")
        if sid in level_ids or sid not in al:
            continue
        events += overlay_beats(ov.get("type"), al[sid]["start"] + 0.15)
    # 2) bespoke-открывашки — заход
    for sid in BESPOKE_STARTS:
        if sid in al:
            st = al[sid]["start"]
            events.append((st + 0.1, "reveal")); events.append((st + 0.5, "impact"))
    # 3) маскот-врезки — вуш
    for sid in MASCOT_SCENES:
        if sid in al:
            events.append((al[sid]["start"], "whoosh"))

    events = [(round(t, 2), c) for t, c in events if t >= 0]
    events.sort()

    seq = pymiere.objects.app.project.activeSequence
    a5, a6 = seq.audioTracks[LONG_TRACK], seq.audioTracks[PT_TRACK]
    for tr in (a5, a6):
        for cl in reversed(list(tr.clips)):
            cl.remove(False, False)

    items, counters = {}, {k: 0 for k in pools}
    def get_item(p):
        if p not in items:
            items[p] = import_media(p)
        return items[p]
    def pick(cat):
        val = pools[cat]; i = counters[cat] % len(val); counters[cat] += 1; return val[i]

    placed = 0
    for (tm, cat) in events:
        it = get_item(pick(cat))
        if it is None:
            continue
        tr = a5 if cat == "reveal" else a6
        try:
            tr.overwriteClip(it, time_from_seconds(tm))
            cl = tr.clips[tr.clips.numItems - 1]
            try: set_clip_volume(cl, SFX_VOL)
            except Exception: pass
            placed += 1
        except Exception:
            pass

    before = (PROJECT / "project_template.prproj").stat().st_mtime
    pymiere.objects.app.project.save(); time.sleep(1.5)
    ok = "OK" if (PROJECT / "project_template.prproj").stat().st_mtime > before else "NO"
    print(f"SFX-битов: {placed} (событий {len(events)}) | БЕЗ уровней | A5=ревилеры A6=точечные | vol={SFX_VOL} | save {ok}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
