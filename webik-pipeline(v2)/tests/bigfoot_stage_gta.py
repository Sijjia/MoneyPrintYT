"""Рендер живой сцены Bigfoot San Andreas (лес, охотники, силуэт → развенчание → GTA V)
+ нарезка по сценам темы 013-022 (каждый срез закрывает свой слот, сцена цельная).
  ../webik-pipeline/.venv/Scripts/python.exe tests/bigfoot_stage_gta.py"""
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import tests.mascot_demo as md

PROJECT = ROOT / "projects" / "2026-09-06_aysberg-gta-temnaya-storona-realnye-dela-vnutriigrovye-tayny"
REMOTION = ROOT / "remotion"
GFX = PROJECT / "assets" / "graphics"; GFX.mkdir(parents=True, exist_ok=True)
VOICE = PROJECT / "assets" / "voice" / "full.mp3"
FPS = 30
COMPOSITION = "BigfootHunt"
ANCHOR = "scene_013"
END_SID = "scene_023"
# фазовые границы (по стартам сцен)
SEG_DEFS = [("hunt", "scene_013", "scene_017"), ("debunk", "scene_017", "scene_021"), ("gtaV", "scene_021", END_SID)]
ACCENT = "#8be04e"


def main() -> int:
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    man = json.loads((PROJECT / "assets" / "images" / "manifest.json").read_text(encoding="utf-8"))
    sc = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    t0 = al[ANCHOR]["start"]; t_end = al[END_SID]["start"]; dur = t_end - t0
    frames = int(dur * FPS)
    rf = lambda sid: int((al[sid]["start"] - t0) * FPS)
    segments = [{"from": rf(a), "to": rf(b), "kind": k} for k, a, b in SEG_DEFS]

    seg_wav = GFX / "_bigfoot_voice.wav"
    subprocess.run(["ffmpeg", "-y", "-ss", f"{t0:.2f}", "-t", f"{dur:.2f}", "-i", str(VOICE),
                    "-ac", "1", "-ar", "22050", str(seg_wav)], capture_output=True)
    mouth = md.mouth_track(seg_wav, dur + 0.2, FPS)

    props = {"mouth": mouth, "segments": segments, "accent": ACCENT, "durationInFrames": frames}
    pf = REMOTION / "_bigfoot.json"; pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    master = GFX / "bigfoot_master.mp4"
    print(f"рендер {COMPOSITION} {dur:.1f}с ({frames}f), фазы {[s['kind'] for s in segments]}", flush=True)
    r = subprocess.run(f'npx remotion render {COMPOSITION} "{os.path.relpath(master, REMOTION).replace(os.sep,"/")}" '
                       f'--props="{os.path.relpath(pf, REMOTION).replace(os.sep,"/")}" --codec=h264 --muted --log=error',
                       cwd=str(REMOTION), shell=True, capture_output=True, text=True)
    pf.unlink(missing_ok=True)
    if not (master.exists() and master.stat().st_size > 100000):
        print(f"✗ рендер упал: {r.stderr[-400:]}"); return 1

    # нарезка по сценам темы
    ids = []
    started = False
    for s in sc:
        if s["id"] == ANCHOR: started = True
        if s["id"] == END_SID: break
        if started and s["id"] in al: ids.append(s["id"])
    bounds = [al[sid]["start"] - t0 for sid in ids] + [dur]
    for i, sid in enumerate(ids):
        a, b = bounds[i], bounds[i + 1]
        out = GFX / f"slice_{sid}.mp4"
        subprocess.run(["ffmpeg", "-y", "-ss", f"{a:.3f}", "-i", str(master), "-t", f"{b - a:.3f}",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-an", str(out)],
                       capture_output=True)
        man[sid] = {"path": str(out.resolve()), "kind": "video", "graphic": "bigfoot_stage", "query": "Bigfoot San Andreas stage"}
        t = PROJECT / "assets" / "video_stock" / "_trimmed" / f"{sid}.mp4"
        if t.exists(): t.unlink()
    (PROJECT / "assets" / "images" / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"✓ {COMPOSITION} {dur:.1f}с → нарезано на {len(ids)} срезов (013-022), манифест обновлён", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
