"""Рендерит спокойный фон под названия тем: реальное фото по теме (или кадр из
архива, если фото нет) → плавный зум Remotion PhotoZoom (без тряски). БЕЗ Premiere.
Читает topic_gaps.json. Выход: assets/topic_bg/{scene}_{start}.mp4 (h264).
Расстановку делает topic_bg_place.py.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT / "projects" / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-"
REMOTION = ROOT / "remotion"
PUB = REMOTION / "public" / "photos"
OUT = (PROJECT / "assets" / "topic_bg").resolve()
STILL = (PROJECT / "assets" / "_topic_still").resolve()


def extract_still(arch: Path, dst: Path) -> bool:
    """Кадр из архива на ~35% длины (мимо чёрного вступления)."""
    if dst.exists() and dst.stat().st_size > 3000:
        return True
    dur = 3.0
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", str(arch)], capture_output=True, text=True)
        dur = float(r.stdout.strip() or 3.0)
    except Exception:
        pass
    ss = max(0.3, dur * 0.35)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{ss:.2f}", "-i", str(arch),
           "-frames:v", "1", "-q:v", "2", str(dst)]
    try:
        subprocess.run(cmd, check=True)
        return dst.exists() and dst.stat().st_size > 3000
    except Exception:
        return False


def main() -> int:
    PUB.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    STILL.mkdir(parents=True, exist_ok=True)
    gaps = json.loads((PROJECT / "topic_gaps.json").read_text(encoding="utf-8"))
    print(f"фонов тем к рендеру: {len(gaps)}")
    ok = 0
    for i, g in enumerate(gaps):
        sid = g["scene_id"]; dur = float(g["dur"]); start = int(float(g["start"]))
        # источник фото
        if g.get("photo") and Path(g["photo"]).exists():
            img = Path(g["photo"])
        else:
            img = STILL / f"{sid}_{start}.jpg"
            if not extract_still(Path(g["arch"]), img):
                print(f"  {sid}: нет фото/кадра — пропуск"); continue
        ext = img.suffix.lower()
        pub = PUB / f"tbg_{sid}_{start}{ext}"
        shutil.copy(img, pub)
        frames = int((dur + 0.4) * 30)
        props = REMOTION / f"_tbg_{sid}_{start}.json"
        props.write_text(json.dumps({"img": f"photos/{pub.name}", "dir": "in",
                                     "durationInFrames": frames}), encoding="utf-8")
        outp = OUT / f"{sid}_{start}_bg.mp4"
        r = subprocess.run(
            f'npx remotion render PhotoZoom "{os.path.relpath(outp, REMOTION)}" '
            f'--props="{os.path.relpath(props, REMOTION)}" --codec=h264 --muted --log=error',
            cwd=str(REMOTION), shell=True, capture_output=True, text=True)
        props.unlink(missing_ok=True)
        if r.returncode == 0 and outp.exists():
            ok += 1; print(f"  ✓ {sid} @ {start//60}:{start%60:02d} ({dur:.1f}с)", flush=True)
        else:
            print(f"  {sid}: FAIL {(r.stderr or '')[-160:]}", flush=True)
    print(f"готово {ok}/{len(gaps)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
