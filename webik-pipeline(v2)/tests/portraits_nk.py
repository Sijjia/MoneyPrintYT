"""Портреты людей на сцены, где они упомянуты (вместо однотипного футажа).
Фетч (Wikipedia+Wikimedia) → PhotoZoom по сценам (ротация фото) → assets/photozoom/{sid}_pz.mp4.
Потом photozoom_swap_nk.py."""
import json, os, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.stocks.wikipedia_photo import WikipediaPhotoClient
from services.stocks.wikimedia import WikimediaClient

PROJECT = ROOT / "projects" / "2026-08-08_aysberg-severnoy-korei-samye-zakrytye-zhutkie-i-maloizvestny"
POR = PROJECT / "assets" / "portraits"; POR.mkdir(parents=True, exist_ok=True)
PUB = ROOT / "remotion" / "public" / "photos"
OUT = PROJECT / "assets" / "photozoom"
REMOTION = ROOT / "remotion"

PEOPLE = [
    {"key": "ilsung", "match": "ким ир сен", "wiki": "Kim Il-sung",
     "wm": ["Kim Il Sung 1950", "Kim Il-sung portrait official"]},
    {"key": "jongil", "match": "ким чен ир", "wiki": "Kim Jong-il",
     "wm": ["Kim Jong-il portrait", "Kim Jong Il 2000"]},
    {"key": "jongun", "match": "ким чен ын", "wiki": "Kim Jong-un", "wm": ["Kim Jong-un portrait"]},
]


def fetch(p):
    wp = WikipediaPhotoClient(); wm = WikimediaClient()
    photos = []
    o = POR / f"{p['key']}_0.jpg"
    try:
        if wp.download_photo(p["wiki"], o) and o.stat().st_size > 5000:
            photos.append(o)
    except Exception as e:
        print(f"  wiki {p['key']}: {str(e)[:50]}")
    for i, q in enumerate(p["wm"], 1):
        o = POR / f"{p['key']}_{i}.jpg"
        try:
            if wm.search_and_download(q, o) and o.stat().st_size > 5000:
                photos.append(o)
        except Exception as e:
            print(f"  wm {p['key']} '{q}': {str(e)[:50]}")
    print(f"  {p['key']}: {len(photos)} фото")
    return photos


def main():
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    PUB.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)

    for p in PEOPLE:
        photos = fetch(p)
        if not photos:
            continue
        # сцены, где назван человек (по всему тексту)
        sids = [s["id"] for s in scenes
                if p["match"] in (s.get("voiceover") or "").lower().replace("  ", " ") and s["id"] in al]
        print(f"  {p['key']}: сцен {len(sids)}")
        for j, sid in enumerate(sids):
            img = photos[j % len(photos)]  # ротация фото
            a = al[sid]; dur = max(2.5, round(a["end"] - a["start"], 1))
            pub = PUB / f"{sid}{img.suffix}"; shutil.copy(img, pub)
            props = REMOTION / f"_pz_{sid}.json"
            props.write_text(json.dumps({"img": f"photos/{sid}{img.suffix}", "dir": "in" if j % 2 else "out",
                                         "durationInFrames": int((dur + 0.5) * 30)}), encoding="utf-8")
            outp = OUT / f"{sid}_pz.mp4"
            if outp.exists() and outp.stat().st_size > 10000:
                print(f"    ⏭ {sid} уже есть"); continue
            r = subprocess.run(f'npx remotion render PhotoZoom "{os.path.relpath(outp, REMOTION)}" '
                               f'--props="{os.path.relpath(props, REMOTION)}" --codec=h264 --muted --log=error',
                               cwd=str(REMOTION), shell=True, capture_output=True, text=True)
            props.unlink(missing_ok=True)
            print(f"    {'✓' if r.returncode == 0 else '✗'} {sid} ({img.name})")
    print("готово — теперь photozoom_swap_nk.py")


if __name__ == "__main__":
    main()
