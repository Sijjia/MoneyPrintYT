"""Добить 2 оставшиеся пары (idx59/idx61): pair-fixer случайно скачал ту же картинку,
что на партнёре. Явно исключаем хеш партнёрского изображения и берём ДРУГОЕ фото.
Рендер ровно в слот → import → overwrite."""
import hashlib, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
from services.stocks.wikimedia import WikimediaClient
from services.premiere_template import timeline_ops as T

PROJECT = ROOT / "projects" / "2026-08-08_aysberg-severnoy-korei-samye-zakrytye-zhutkie-i-maloizvestny"
PHOTOS = ROOT / "remotion" / "public" / "photos"
OUT = PROJECT / "assets" / "photozoom"
REMOTION = ROOT / "remotion"

# (idx второго клипа, sid, avoid-файл партнёра, start, dur, набор запросов)
TASKS = [
    (59, "scene_062", PHOTOS / "scene_062.jpg", 421.5, 5.3,
     ["Kijong-dong flagpole tower", "North Korea propaganda village Kijong",
      "DMZ North Korea guard post", "Panmunjom North side", "North Korea empty apartments"]),
    (61, "scene_064", PHOTOS / "scene_064.jpg", 430.1, 7.7,
     ["North Korea deserted village fields", "DMZ demilitarized zone landscape Korea",
      "North Korea rural countryside", "North Korea farmland propaganda", "Korea border fence"]),
]


def md5f(p):
    try:
        return hashlib.md5(Path(p).read_bytes()).hexdigest()[:12]
    except Exception:
        return None


def main() -> int:
    wm = WikimediaClient()
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[2]
    tmp = Path(tempfile.mkdtemp())
    ok = 0
    for idx, sid, avoid, st, dur, queries in TASKS:
        used = {md5f(avoid)}
        used.discard(None)
        frames = max(45, round(dur * 30))
        chosen = None
        for q in queries:
            try:
                hits = wm.search_images(q, limit=15, min_width=1000)
            except Exception:
                hits = []
            for j, hit in enumerate(hits):
                o = tmp / f"c_{idx}_{j}.jpg"
                try:
                    wm.download(hit, o)
                    h = md5f(o)
                except Exception:
                    continue
                if h and h not in used:
                    chosen = o; break
            if chosen:
                print(f"  фото для idx={idx} {sid}: q='{q[:40]}'"); break
        if not chosen:
            print(f"  ✗ idx={idx}: не нашёл отличное фото"); continue
        pub = PHOTOS / f"{sid}_p3.jpg"; shutil.copy(chosen, pub)
        props = REMOTION / f"_pz_{sid}_p3.json"
        props.write_text(json.dumps({"img": f"photos/{sid}_p3.jpg", "dir": "out",
                                     "durationInFrames": int(frames)}), encoding="utf-8")
        outp = OUT / f"{sid}_p3_pz.mp4"
        r = subprocess.run(f'npx remotion render PhotoZoom "{os.path.relpath(outp, REMOTION)}" '
                           f'--props="{os.path.relpath(props, REMOTION)}" --codec=h264 --muted --log=error',
                           cwd=str(REMOTION), shell=True, capture_output=True, text=True)
        props.unlink(missing_ok=True)
        if r.returncode != 0:
            print(f"  ✗ render idx={idx}:", (r.stderr or "")[-150:]); continue
        item = T.import_media(outp)
        if item is None:
            print(f"  ✗ import idx={idx}"); continue
        T.place_clip(v3, item, st, overwrite=True)
        ok += 1
        print(f"  ✓ idx={idx} {sid} → {outp.name}")
    pymiere.objects.app.project.save()
    print(f"\nготово: {ok}/2; проект сохранён")
    return 0


if __name__ == "__main__":
    sys.exit(main())
