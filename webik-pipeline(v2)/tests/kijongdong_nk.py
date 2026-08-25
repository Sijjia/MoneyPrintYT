"""Архив-фото Кичжондона (фейк-деревня) вместо однотипного youtube-футажа.
Фетч Wikimedia → PhotoZoom по сценам топика (ротация) → assets/photozoom/{sid}_pz.mp4. Потом swap."""
import json, os, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.stocks.wikimedia import WikimediaClient

PROJECT = ROOT / "projects" / "2026-08-08_aysberg-severnoy-korei-samye-zakrytye-zhutkie-i-maloizvestny"
POR = PROJECT / "assets" / "portraits"; POR.mkdir(parents=True, exist_ok=True)
PUB = ROOT / "remotion" / "public" / "photos"
OUT = PROJECT / "assets" / "photozoom"
REMOTION = ROOT / "remotion"

QUERIES = [
    "Kijong-dong", "Kijong-dong flagpole", "Panmunjom North Korea",
    "Korean Demilitarized Zone village", "Daeseong-dong Kijong-dong",
]
# youtube-auto сцены топика Кичжондон, которые меняем на архив-фото
SIDS = ["scene_057", "scene_058", "scene_059", "scene_060", "scene_063",
        "scene_065", "scene_066", "scene_067", "scene_068"]


def main():
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    wm = WikimediaClient()
    photos = []
    for i, q in enumerate(QUERIES):
        o = POR / f"kijong_{i}.jpg"
        try:
            if wm.search_and_download(q, o) and o.stat().st_size > 5000:
                photos.append(o); print(f"  ✓ '{q}' → {o.name}")
        except Exception as e:
            print(f"  ✗ '{q}': {str(e)[:50]}")
    if not photos:
        print("нет фото Кичжондона — прерываю"); return
    print(f"фото: {len(photos)}")
    PUB.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
    for j, sid in enumerate(SIDS):
        if sid not in al:
            continue
        img = photos[j % len(photos)]
        a = al[sid]; dur = max(2.5, round(a["end"] - a["start"], 1))
        pub = PUB / f"{sid}{img.suffix}"; shutil.copy(img, pub)
        props = REMOTION / f"_pz_{sid}.json"
        props.write_text(json.dumps({"img": f"photos/{sid}{img.suffix}", "dir": "in" if j % 2 else "out",
                                     "durationInFrames": int((dur + 0.5) * 30)}), encoding="utf-8")
        outp = OUT / f"{sid}_pz.mp4"
        r = subprocess.run(f'npx remotion render PhotoZoom "{os.path.relpath(outp, REMOTION)}" '
                           f'--props="{os.path.relpath(props, REMOTION)}" --codec=h264 --muted --log=error',
                           cwd=str(REMOTION), shell=True, capture_output=True, text=True)
        props.unlink(missing_ok=True)
        print(f"    {'✓' if r.returncode == 0 else '✗'} {sid} ({img.name})")
    print("готово — теперь photozoom_swap_nk.py")


if __name__ == "__main__":
    main()
