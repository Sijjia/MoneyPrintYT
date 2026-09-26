"""Обобщённый рендер bespoke-сцены GTA: рендерит Remotion-композицию на весь отрезок темы
с липсинком капибары + нарезает на срезы по сценам темы (каждый закрывает слот).
Конфиг через env:
  BS_COMP=UFOScene BS_ANCHOR=scene_062 BS_END=scene_072 BS_ACCENT=#5ef0c8
  BS_SEGS='[["ufos","scene_062","scene_068"],["sunken","scene_068","scene_070"],["confirmed","scene_070","scene_072"]]'
  BS_TAG=ufo   (префикс для файлов срезов/мастера)
  ../webik-pipeline/.venv/Scripts/python.exe tests/bespoke_stage_gta.py"""
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


def main() -> int:
    comp = os.environ["BS_COMP"]; anchor = os.environ["BS_ANCHOR"]; end_sid = os.environ["BS_END"]
    accent = os.environ.get("BS_ACCENT", "#5ef0c8"); tag = os.environ.get("BS_TAG", comp.lower())
    seg_defs = json.loads(os.environ["BS_SEGS"])

    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    man = json.loads((PROJECT / "assets" / "images" / "manifest.json").read_text(encoding="utf-8"))
    sc = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    t0 = al[anchor]["start"]; t_end = al[end_sid]["start"]; dur = t_end - t0
    frames = int(dur * FPS)
    rf = lambda sid: int((al[sid]["start"] - t0) * FPS)
    segments = [{"from": rf(a), "to": rf(b), "kind": k} for k, a, b in seg_defs]

    seg_wav = GFX / f"_{tag}_voice.wav"
    subprocess.run(["ffmpeg", "-y", "-ss", f"{t0:.2f}", "-t", f"{dur:.2f}", "-i", str(VOICE),
                    "-ac", "1", "-ar", "22050", str(seg_wav)], capture_output=True)
    mouth = md.mouth_track(seg_wav, dur + 0.2, FPS)

    props = {"mouth": mouth, "segments": segments, "accent": accent, "durationInFrames": frames}
    pf = REMOTION / f"_{tag}.json"; pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    master = GFX / f"{tag}_master.mp4"
    print(f"рендер {comp} {dur:.1f}с ({frames}f), фазы {[s['kind'] for s in segments]}", flush=True)
    r = subprocess.run(f'npx remotion render {comp} "{os.path.relpath(master, REMOTION).replace(os.sep,"/")}" '
                       f'--props="{os.path.relpath(pf, REMOTION).replace(os.sep,"/")}" --codec=h264 --muted --log=error',
                       cwd=str(REMOTION), shell=True, capture_output=True, text=True)
    pf.unlink(missing_ok=True)
    if not (master.exists() and master.stat().st_size > 100000):
        print(f"✗ рендер упал: {r.stderr[-400:]}"); return 1

    ids, started = [], False
    for s in sc:
        if s["id"] == anchor: started = True
        if s["id"] == end_sid: break
        if started and s["id"] in al: ids.append(s["id"])
    bounds = [al[sid]["start"] - t0 for sid in ids] + [dur]
    for i, sid in enumerate(ids):
        a, b = bounds[i], bounds[i + 1]
        out = GFX / f"slice_{sid}.mp4"
        subprocess.run(["ffmpeg", "-y", "-ss", f"{a:.3f}", "-i", str(master), "-t", f"{b - a:.3f}",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-an", str(out)],
                       capture_output=True)
        man[sid] = {"path": str(out.resolve()), "kind": "video", "graphic": tag, "query": comp}
        t = PROJECT / "assets" / "video_stock" / "_trimmed" / f"{sid}.mp4"
        if t.exists(): t.unlink()
    (PROJECT / "assets" / "images" / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"✓ {comp} → {len(ids)} срезов ({anchor}..{end_sid}), манифест обновлён", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
