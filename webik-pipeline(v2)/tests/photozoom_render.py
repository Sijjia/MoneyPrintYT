"""Рендер плавного зума (Remotion PhotoZoom) для ВСЕХ фото-сцен вместо трясущегося
ffmpeg-Ken-Burns. Копирует исходники в remotion/public/photos/, рендерит h264.
Видео-сцены (_fig/_arch/_yt) не трогаем. Потом photozoom_swap.py.
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
OUT = PROJECT / "assets" / "photozoom"
RP = PROJECT / "assets" / "real_photos"
IMG = PROJECT / "assets" / "images"

# реальные фото (перекрывают параллакс-wm)
REAL = {
    "scene_007": RP / "kuzya_popov.jpg", "scene_012": RP / "kuzya_monastery.jpg", "scene_016": RP / "kuzya_monastery.jpg",
    "scene_022": RP / "penza_kuznetsov1.webp", "scene_025": RP / "penza_kuznetsov2.webp",
    "scene_099": RP / "family_children.jpg", "scene_127": RP / "anthill_theriault.jpg",
    "scene_168": RP / "china_protest.jpg", "scene_172": RP / "colonia_hotel.jpg", "scene_173": REMOTION / "public" / "schafer.jpg",
    "scene_187": RP / "solar_sirius.jpg",
    "scene_083": RP / "nigeria_almajiri1.jpg", "scene_085": RP / "nigeria_almajiri2.jpg",
    "scene_090": RP / "jain_temple.jpg", "scene_092": RP / "jain_nun.jpg", "scene_093": RP / "jain_temple.jpg",
    "scene_095": RP / "jain_pilgrimage.jpg", "scene_109": RP / "shakahola_kilifi.jpg",
    "scene_101": RP / "family_Lake_Eildon_late_2011.jpg", "scene_104": RP / "family_Sherbrooke_Forest.jpg",
    "scene_170": RP / "colonia_hotel.jpg", "scene_171": RP / "colonia_villa.jpg", "scene_164": RP / "china_protest.jpg",
    "scene_177": RP / "albino_tz_school.jpg", "scene_181": RP / "albino_salif.jpg",
}


def build_map():
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    m = {}
    # параллакс-wm (start>59)
    for line in (PROJECT / "_parallax_list.txt").read_text(encoding="utf-8").splitlines():
        sid = line.split("|")[0]
        if al.get(sid, {}).get("start", 0) < 59:
            continue
        wm = IMG / f"{sid}_wm.jpg"
        if wm.exists():
            m[sid] = wm
    m.update(REAL)  # реальные перекрывают
    # длительности
    out = {}
    for sid, img in m.items():
        v = al.get(sid)
        if not v or not Path(img).exists():
            continue
        out[sid] = (Path(img), max(2.5, round(v["end"] - v["start"], 1)))
    return out


def main() -> int:
    PUB.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    m = build_map()
    print(f"фото-сцен к рендеру: {len(m)}")
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
    print(f"готово {ok}/{len(m)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
