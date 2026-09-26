"""EN-рендер bespoke-графики GTA (records + Bigfoot/UFO/Kurtaj-открывашки) с АНГЛИЙСКИМ текстом
и EN-таймингом (голос Brian). Рендерит мастер, режет по сценам, обновляет EN-манифест.
  ../webik-pipeline/.venv/Scripts/python.exe tests/bespoke_en_gta.py"""
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import tests.mascot_demo as md

EN = ROOT / "projects" / "2026-09-06_aysberg-gta-temnaya-storona-realnye-dela-vnutriigrovye-tayny_EN"
REMOTION = ROOT / "remotion"
GFX = EN / "assets" / "graphics"; GFX.mkdir(parents=True, exist_ok=True)
VOICE = EN / "assets" / "voice" / "full.mp3"
FPS = 30
al = json.loads((EN / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
man = json.loads((EN / "assets" / "images" / "manifest.json").read_text(encoding="utf-8"))
sc = json.loads((EN / "scenes.json").read_text(encoding="utf-8"))["scenes"]


def mouth_for(t0, dur):
    w = GFX / "_m.wav"
    subprocess.run(["ffmpeg", "-y", "-ss", f"{t0:.2f}", "-t", f"{dur:.2f}", "-i", str(VOICE),
                    "-ac", "1", "-ar", "22050", str(w)], capture_output=True)
    return md.mouth_track(w, dur + 0.2, FPS)


def render(comp, props, frames, name):
    props = dict(props); props["durationInFrames"] = frames
    pf = REMOTION / f"_en_{name}.json"; pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    out = GFX / f"{name}_master.mp4"
    print(f"рендер {comp} EN {frames/FPS:.1f}с", flush=True)
    r = subprocess.run(f'npx remotion render {comp} "{os.path.relpath(out, REMOTION).replace(os.sep,"/")}" '
                       f'--props="{os.path.relpath(pf, REMOTION).replace(os.sep,"/")}" --codec=h264 --muted --log=error',
                       cwd=str(REMOTION), shell=True, capture_output=True, text=True)
    pf.unlink(missing_ok=True)
    if not (out.exists() and out.stat().st_size > 100000):
        print(f"  ✗ {name}: {r.stderr[-300:]}"); return None
    return out


def slice_and_manifest(master, anchor, slice_ids, graphic):
    t0 = al[anchor]["start"]
    ids_all = []
    started = False
    end_after = slice_ids[-1]
    for s in sc:
        if s["id"] == anchor: started = True
        if started: ids_all.append(s["id"])
        if s["id"] == end_after: break
    # границы срезов по нужным сценам
    for i, sid in enumerate(slice_ids):
        a = al[sid]["start"] - t0
        nxt = slice_ids[i + 1] if i + 1 < len(slice_ids) else None
        b = (al[nxt]["start"] - t0) if nxt else (al[ids_all[ids_all.index(sid) + 1]]["start"] - t0
                                                 if ids_all.index(sid) + 1 < len(ids_all) else a + 6)
        out = GFX / f"slice_{sid}.mp4"
        subprocess.run(["ffmpeg", "-y", "-ss", f"{a:.3f}", "-i", str(master), "-t", f"{b-a:.3f}",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-an", str(out)],
                       capture_output=True)
        man[sid] = {"path": str(out.resolve()), "kind": "video", "graphic": graphic, "query": graphic}
        (EN / "assets" / "video_stock" / "_trimmed" / f"{sid}.mp4").unlink(missing_ok=True)
    print(f"  ✓ {graphic}: срезов {len(slice_ids)} ({slice_ids[0]}..{slice_ids[-1]})", flush=True)


def main() -> int:
    # ── RECORDS (вся первая тема 008-012) ──
    rf = lambda a, t0: int((al[a]["start"] - t0) * FPS)
    t0 = al["scene_008"]["start"]; dur = al["scene_013"]["start"] - t0
    segs = [
        {"from": 0, "to": rf("scene_010", t0), "kind": "views", "value": 90421491,
         "label": "VIEWS IN 24 HOURS", "sub": "GTA VI trailer · Guinness record"},
        {"from": rf("scene_010", t0), "to": rf("scene_011", t0), "kind": "cash", "value": 800000000, "prefix": "$",
         "label": "ON THE FIRST DAY", "sub": "GTA V · 2013"},
        {"from": rf("scene_011", t0), "to": rf("scene_012", t0), "kind": "stacks", "value": 6000000000, "prefix": "$",
         "label": "TOTAL REVENUE BY 2018", "sub": "GTA Online — hundreds of millions a year"},
        {"from": rf("scene_012", t0), "to": int(dur * FPS), "kind": "discs", "value": 200000000,
         "label": "COPIES SOLD", "sub": "across all platforms"},
    ]
    m = render("GTARecordsStage", {"mouth": mouth_for(t0, dur), "segments": segs, "accent": "#ff2d78", "accent2": "#25e0c8"},
               int(dur * FPS), "records")
    if m: slice_and_manifest(m, "scene_008", [f"scene_{n:03d}" for n in range(8, 13)], "records_stage")

    # ── BIGFOOT intro (013-014) ──
    t0 = al["scene_013"]["start"]; dur = al["scene_023"]["start"] - t0
    segs = [{"from": 0, "to": rf("scene_017", t0), "kind": "hunt"},
            {"from": rf("scene_017", t0), "to": rf("scene_021", t0), "kind": "debunk"},
            {"from": rf("scene_021", t0), "to": int(dur * FPS), "kind": "gtaV"}]
    Lbf = {"hunt": {"t": "A LEGEND HUNTED FOR YEARS", "s": "San Andreas · 2004"},
           "debunk": {"t": "THERE WAS NO BIGFOOT", "s": "every screenshot was photoshop or a mod"},
           "gtaV": {"t": "A REWARD IN GTA V", "s": "…and it was a man in a suit"}}
    m = render("BigfootHunt", {"mouth": mouth_for(t0, dur), "segments": segs, "accent": "#8be04e", "L": Lbf}, int(dur * FPS), "bigfoot")
    if m: slice_and_manifest(m, "scene_013", ["scene_013", "scene_014"], "intro")

    # ── UFO intro (062-063) ──
    t0 = al["scene_062"]["start"]; dur = al["scene_072"]["start"] - t0
    segs = [{"from": 0, "to": rf("scene_068", t0), "kind": "ufos"},
            {"from": rf("scene_068", t0), "to": rf("scene_070", t0), "kind": "sunken"},
            {"from": rf("scene_070", t0), "to": int(dur * FPS), "kind": "confirmed"}]
    Lufo = {"ufos": {"t": "THREE UFOs AT 100%", "s": "Chiliad · Sandy Shores · Fort Zancudo"},
            "sunken": {"t": "THE SUNKEN SAUCER", "s": "on the ocean floor · deep-sea gear required"},
            "confirmed": {"t": "CONFIRMED BY ROCKSTAR", "s": "the Chiliad mural link is still a mystery"}}
    m = render("UFOScene", {"mouth": mouth_for(t0, dur), "segments": segs, "accent": "#5ef0c8", "L": Lufo,
                            "segTxt": "= anagram of 'EASTER EGG'"}, int(dur * FPS), "ufo")
    if m: slice_and_manifest(m, "scene_062", ["scene_062", "scene_063"], "intro")

    # ── KURTAJ intro (160-161) ──
    t0 = al["scene_160"]["start"]; dur = al["scene_168"]["start"] - t0
    segs = [{"from": 0, "to": rf("scene_164", t0), "kind": "breach"},
            {"from": rf("scene_164", t0), "to": rf("scene_166", t0), "kind": "leak"},
            {"from": rf("scene_166", t0), "to": int(dur * FPS), "kind": "verdict"}]
    Lk = {"breach": {"t": "HACKED WITH A FIRE STICK", "s": "18 · Lapsus$ · on bail, from a hotel room"},
          "verdict": {"t": "SENTENCE: INDEFINITE HOSPITAL ORDER", "s": "found unfit · Dec 2023 · + Uber hack"}}
    m = render("KurtajHack", {"mouth": mouth_for(t0, dur), "segments": segs, "accent": "#37e0a0", "L": Lk,
                             "fireLabel": "Fire Stick + hotel phone →", "leakLabel": "GTA VI CLIPS LEAKED",
                             "leakSub": "the biggest leak in gaming history"}, int(dur * FPS), "kurtaj")
    if m: slice_and_manifest(m, "scene_160", ["scene_160", "scene_161"], "intro")

    (EN / "assets" / "images" / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    print("EN-манифест обновлён (bespoke срезы)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
