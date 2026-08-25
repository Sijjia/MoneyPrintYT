"""НК: перегон 3D-parallax фото-сцен в чистый PhotoZoom (плавный зум без искажений).
Список сцен строим из manifest (path в assets/parallax) → исходный jpg → Remotion PhotoZoom.
Потом photozoom_swap_nk.py.
"""
import json, os, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT / "projects" / "2026-08-08_aysberg-severnoy-korei-samye-zakrytye-zhutkie-i-maloizvestny"
REMOTION = ROOT / "remotion"
PUB = REMOTION / "public" / "photos"
OUT = PROJECT / "assets" / "photozoom"
IMG = PROJECT / "assets" / "images"


def build_map():
    m = json.loads((PROJECT / "assets" / "images" / "manifest.json").read_text(encoding="utf-8"))
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    out = {}
    for sid, v in m.items():
        p = (v.get("path") or "").replace("\\", "/")
        if "parallax" not in p:
            continue
        # исходное фото: сначала _wm.jpg (wikimedia), иначе {sid}.jpg (pexels)
        src = IMG / f"{sid}_wm.jpg"
        if not src.exists():
            src = IMG / f"{sid}.jpg"
        a = al.get(sid)
        if not (src.exists() and a):
            continue
        dur = max(2.5, round(a["end"] - a["start"], 1))
        out[sid] = (src, dur)
    return out


def main() -> int:
    PUB.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    m = build_map()
    print(f"parallax фото-сцен к перегону в PhotoZoom: {len(m)}")
    ok = 0
    for i, (sid, (img, dur)) in enumerate(sorted(m.items())):
        ext = img.suffix.lower()
        pub = PUB / f"{sid}{ext}"
        shutil.copy(img, pub)
        frames = int((dur + 0.5) * 30)
        d = "in" if i % 2 == 0 else "out"
        props = REMOTION / f"_pz_{sid}.json"
        props.write_text(json.dumps({"img": f"photos/{sid}{ext}", "dir": d, "durationInFrames": frames}), encoding="utf-8")
        outp = OUT / f"{sid}_pz.mp4"
        r = subprocess.run(
            f'npx remotion render PhotoZoom "{os.path.relpath(outp, REMOTION)}" '
            f'--props="{os.path.relpath(props, REMOTION)}" --codec=h264 --muted --log=error',
            cwd=str(REMOTION), shell=True, capture_output=True, text=True)
        props.unlink(missing_ok=True)
        if r.returncode == 0 and outp.exists():
            ok += 1
        else:
            print(f"  {sid}: FAIL {(r.stderr or '')[-160:]}")
        if (i + 1) % 10 == 0:
            print(f"  ...{i+1}/{len(m)} ({ok} ok)")
    print(f"готово: {ok}/{len(m)} PhotoZoom .mp4 → {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
