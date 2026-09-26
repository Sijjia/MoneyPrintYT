"""SFX-хореография Adult Swim: биты по оверлеям (overlays.json) + карточки уровней (ревилер+бум)
+ ARG/Бостон (глитч-удары). Пулы assets/sfx: w вуши, t тики, i удары, r ревилеры.
Ставит на A5 (idx4, ревилеры) / A6 (idx5, точечные), тихо. Ротация без повторов.
  ../webik-pipeline/.venv/Scripts/python.exe tests/sfx_choreograph_as.py
"""
import glob, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
from pymiere.wrappers import time_from_seconds
from services.premiere_template.timeline_ops import import_media
from tests.assemble_iceberg_test import set_clip_volume

PROJECT = ROOT / "projects" / "2026-09-05_aysberg-robloks-temnaya-skrytaya-storona-realnye-intsidenty-"
SFX = (PROJECT / "assets" / "sfx").resolve()
LONG_TRACK = 4   # A5 — ревилеры
PT_TRACK = 5     # A6 — точечные
SFX_VOL = 0.55
ARG_SCENES = set(["scene_001", "scene_003", "scene_040", "scene_083", "scene_093", "scene_095", "scene_098", "scene_099", "scene_103", "scene_104", "scene_108", "scene_125", "scene_126", "scene_137", "scene_148", "scene_152", "scene_154", "scene_160", "scene_169", "scene_172", "scene_174", "scene_177", "scene_185", "scene_228"])


def pool(prefix):
    return sorted(Path(p) for p in glob.glob(str(SFX / f"{prefix}[0-9]*.wav")))


def overlay_beats(otype, s):
    """биты по типу оверлея"""
    if otype == "stat":
        return [(s + 0.15, "impact")]
    if otype == "timeline":
        return [(s + 0.4, "tick"), (s + 1.1, "tick"), (s + 1.8, "tick")]
    if otype == "compare":
        return [(s, "whoosh"), (s + 0.7, "impact")]
    if otype == "quote":
        return [(s, "tick")]
    if otype in ("name", "phrase", "evidence"):
        return [(s, "whoosh")]
    return [(s, "whoosh")]


def main() -> int:
    pools = {"whoosh": pool("w"), "tick": pool("t"), "impact": pool("i"), "reveal": pool("r")}
    for k, val in pools.items():
        print(f"  пул {k}: {len(val)}")
        if not val:
            print("  ПУСТО — сначала скопируй пул в assets/sfx"); return 1

    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    overlays = json.loads((PROJECT / "overlays.json").read_text(encoding="utf-8"))["overlays"]

    events = []
    # 1) оверлеи
    for ov in overlays:
        events += overlay_beats(ov.get("type"), float(ov["start"]))
    # 2) карточки уровней → ревилер + глубокий бум
    for s in scenes:
        if (s.get("visual") or {}).get("type") == "level_card" and s["id"] in al:
            st = al[s["id"]]["start"]
            events.append((st, "reveal")); events.append((st + 0.5, "impact"))
    # 3) ARG-сцены + Бостон → глитч-удар + тик
    for sid in ARG_SCENES:
        if sid in al:
            st = al[sid]["start"]
            events.append((st + 0.1, "impact")); events.append((st + 0.6, "tick"))

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
            # громкость последнего уложенного клипа
            cl = tr.clips[tr.clips.numItems - 1]
            try: set_clip_volume(cl, SFX_VOL)
            except Exception: pass
            placed += 1
        except Exception:
            pass

    before = (PROJECT / "project_template.prproj").stat().st_mtime
    pymiere.objects.app.project.save(); time.sleep(1.5)
    ok = "OK" if (PROJECT / "project_template.prproj").stat().st_mtime > before else "NO"
    print(f"SFX-битов: {placed} (событий {len(events)}) | A5=ревилеры A6=точечные | vol={SFX_VOL} | save {ok}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
