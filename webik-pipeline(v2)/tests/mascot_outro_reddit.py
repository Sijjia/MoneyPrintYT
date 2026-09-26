"""Аутро через маскота: рендер MascotOutro (капибара + CTA-кнопки под голос) и ТОЧЕЧНАЯ
укладка на V3 поверх CTA-сцен (без пересборки). Premiere открыт.
  ../webik-pipeline/.venv/Scripts/python.exe tests/mascot_outro_gta.py"""
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
from pymiere.wrappers import time_from_seconds
import tests.mascot_demo as md
from services.premiere_template.timeline_ops import import_media

PROJECT = ROOT / "projects" / "2026-09-13_aysberg-reddit-strannaya-i-trevozhnaya-storona"
REMOTION = ROOT / "remotion"
GFX = PROJECT / "assets" / "graphics"; GFX.mkdir(parents=True, exist_ok=True)
VOICE = PROJECT / "assets" / "voice" / "full.mp3"
FPS = 30
V3 = 2
ANCHOR = "scene_239"
# сегменты по CTA-сценам
SEG_DEFS = [("bye", "scene_239", None)]


def main() -> int:
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    t0 = al[ANCHOR]["start"]
    seq = pymiere.objects.app.project.activeSequence
    # конец по ГОЛОСУ (не seq.end — секвенция держит старую фикс. длину и не ужимается)
    import subprocess as _sp
    _r = _sp.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(VOICE)],
                 capture_output=True, text=True)
    t_end = float(_r.stdout.strip())
    dur = t_end - t0
    frames = int(dur * FPS)
    rf = lambda sid: int((al[sid]["start"] - t0) * FPS)
    segments = [{"from": rf(a), "to": (rf(b) if b else frames), "kind": k} for k, a, b in SEG_DEFS]

    seg_wav = GFX / "_outro_voice.wav"
    subprocess.run(["ffmpeg", "-y", "-ss", f"{t0:.2f}", "-t", f"{dur:.2f}", "-i", str(VOICE),
                    "-ac", "1", "-ar", "22050", str(seg_wav)], capture_output=True)
    mouth = md.mouth_track(seg_wav, dur + 0.2, FPS)

    props = {"mouth": mouth, "segments": segments, "accent": "#ff2d55", "durationInFrames": frames}
    pf = REMOTION / "_mascot_outro.json"; pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    out = GFX / "mascot_outro.mp4"
    print(f"рендер MascotOutro {dur:.1f}с ({frames}f)", flush=True)
    r = subprocess.run(f'npx remotion render MascotOutro "{os.path.relpath(out, REMOTION).replace(os.sep,"/")}" '
                       f'--props="{os.path.relpath(pf, REMOTION).replace(os.sep,"/")}" --codec=h264 --muted --log=error',
                       cwd=str(REMOTION), shell=True, capture_output=True, text=True)
    pf.unlink(missing_ok=True)
    if not (out.exists() and out.stat().st_size > 80000):
        print(f"✗ рендер упал: {r.stderr[-400:]}"); return 1

    # точечная укладка на V3 поверх CTA
    item = import_media(out.resolve())
    if item is None:
        print("✗ import"); return 1
    v3 = seq.videoTracks[V3]
    # снап на фактический старт клипа (иначе остаётся огрызок-мелькание базовой сцены перед аутро)
    starts = [c.start.seconds for c in v3.clips]
    near = min(starts, key=lambda s: abs(s - t0)) if starts else t0
    if abs(near - t0) < 0.6:
        t0 = near
    v3.overwriteClip(item, time_from_seconds(t0))
    pymiere.objects.app.project.save()
    print(f"✓ аутро-маскот уложен на V3 @ {int(t0//60)}:{int(t0%60):02d} ({dur:.1f}с), сохранено", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
