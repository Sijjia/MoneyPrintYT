"""Замена кривого зум-фото на сценах 036/038 Adult Swim:
  036 → bespoke-графика BreakingAlert (Бостон 2007: тревога сапёров → разоблачение LED-рекламы).
  038 → МАСКОТ с липсинком под голос сцены + улика-кадр (вводим маскота точечно).
Рендерит base-media и подменяет клип на живом таймлайне (changeMediaPath). Premiere открыт.
  ../webik-pipeline/.venv/Scripts/python.exe tests/fix_036_038_as.py
"""
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
import tests.assemble_as as A
import tests.mascot_demo as md

PROJECT = A.PROJECT_DIR
REMOTION = ROOT / "remotion"
GFX = PROJECT / "assets" / "gfx"
GFX.mkdir(parents=True, exist_ok=True)
PUBM = REMOTION / "public" / "mascot"
PUBM.mkdir(parents=True, exist_ok=True)
VOICE = PROJECT / "assets" / "voice" / "full.mp3"
TRIMMED = A.TRIMMED_DIR
tps = 254016000000
FPS = 30


def cstart(c):
    return c.start.seconds if hasattr(c.start, "seconds") else float(c.start.ticks) / tps


def render_remotion(comp, props, out, frames):
    props["durationInFrames"] = frames
    pf = REMOTION / f"_fix_{out.stem}.json"
    pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run(f'npx remotion render {comp} "{os.path.relpath(out, REMOTION).replace(os.sep,"/")}" '
                       f'--props="{os.path.relpath(pf, REMOTION).replace(os.sep,"/")}" --codec=h264 --muted --log=error',
                       cwd=str(REMOTION), shell=True, capture_output=True, text=True)
    pf.unlink(missing_ok=True)
    if not (out.exists() and out.stat().st_size > 20000):
        print(f"  ✗ render {comp}: {(r.stderr or r.stdout)[-200:]}")
        return False
    return True


def main() -> int:
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    man = json.loads((PROJECT / "assets" / "images" / "manifest.json").read_text(encoding="utf-8"))

    # --- 036: BreakingAlert (Бостон) ---
    d36 = al["scene_036"]["end"] - al["scene_036"]["start"]
    out36 = GFX / "scene_036_alert.mp4"
    ok36 = render_remotion("BreakingAlert", {
        "kicker": "СРОЧНО",
        "headline": "БОСТОН ПАРАЛИЗОВАН: ПОДОЗРИТЕЛЬНЫЕ УСТРОЙСТВА В 10 ГОРОДАХ",
        "cities": 10,
        "reveal": "Это была реклама мультфильма про говорящую котлету.",
        "stamp": "ЭТО БЫЛА РЕКЛАМА",
        "showMooninite": True,
    }, out36, int(d36 * FPS) + 30)

    # --- 038: маскот с липсинком + улика ---
    d38 = al["scene_038"]["end"] - al["scene_038"]["start"]
    seg = GFX / "seg_038.wav"
    subprocess.run(["ffmpeg", "-y", "-ss", f"{al['scene_038']['start']:.2f}", "-t", f"{d38:.2f}",
                    "-i", str(VOICE), "-ac", "1", "-ar", "22050", str(seg)], capture_output=True)
    mouth = md.mouth_track(seg, d38 + 0.2, FPS)
    # улика: кадр сапёров/эвакуации из соседней сцены 034
    comp = []
    src34 = TRIMMED / "scene_034_dd2.mp4"
    if not src34.exists():
        src34 = TRIMMED / "scene_034.mp4"
    cf = PUBM / "as038_eco.jpg"
    if src34.exists() and md.grab_frame(src34, cf):
        comp = [{"src": "mascot/as038_eco.jpg", "x": 0.72, "y": 0.36, "w": 640, "from": 12, "to": len(mouth) - 6}]
    out38 = GFX / "scene_038_mascot.mp4"
    ok38 = render_remotion("Mascot", {
        "mouth": mouth, "position": "left", "scale": 0.95, "jitter": 0.8,
        "companions": comp, "caption": "Крупнейший провал — и символ эпохи.",
        "accent": "#e11d1d",
    }, out38, len(mouth))

    # --- подмена на V3 ---
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[A.PARALLAX_VIDEO_TRACK_IDX]
    clip_at = {}
    for i in range(v3.clips.numItems):
        clip_at.setdefault(round(cstart(v3.clips[i]), 1), i)

    def swap(sid, out, ok):
        if not ok:
            print(f"  ✗ {sid}: рендер не готов"); return
        st = al[sid]["start"]
        idx = None
        for d in (0.0, 0.1, -0.1, 0.2, -0.2, 0.3, -0.3, 0.4, -0.4):
            idx = clip_at.get(round(st + d, 1))
            if idx is not None:
                break
        if idx is None:
            print(f"  ✗ {sid}: клип на V3 не найден @ {st:.1f}"); return
        try:
            v3.clips[idx].projectItem.changeMediaPath(str(out.resolve()), True)
            man[sid] = {"path": str(out), "query": "bespoke gfx", "kind": "video", "source": "gfx-fix"}
            print(f"  ✓ {sid} ← {out.name}", flush=True)
        except Exception as e:
            print(f"  ✗ {sid}: swap {str(e)[:50]}")

    swap("scene_036", out36, ok36)
    swap("scene_038", out38, ok38)

    (PROJECT / "assets" / "images" / "manifest.json").write_text(
        json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    pymiere.objects.app.project.save()
    print("сохранено", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
