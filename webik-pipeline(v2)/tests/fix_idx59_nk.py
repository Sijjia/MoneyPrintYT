"""Последняя коллизия: idx59 совпал с соседом idx60 (пул фото Кичжондона крошечный).
Берём глобальный avoid-set = хеши ИСХОДНИКОВ ВСЕХ клипов V3, ищем отличное НК-фото
(широкие запросы), рендерим ровно в слот → import → overwrite idx59."""
import hashlib, json, os, re, shutil, subprocess, sys, tempfile
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
IDX, SID, START, DUR = 59, "scene_062", 421.5, 5.3
QUERIES = ["North Korea watchtower DMZ", "Panmunjom truce village", "North Korea loudspeaker propaganda",
           "North Korea border guard post", "North Korea concrete apartment blocks",
           "North Korea military checkpoint", "North Korea barbed wire fence", "Pyongyang empty street"]


def md5f(p):
    try:
        return hashlib.md5(Path(p).read_bytes()).hexdigest()[:12]
    except Exception:
        return None


def source_for(path):
    b = os.path.basename(path)
    m = re.match(r"(scene_\d+(?:_[a-z0-9]+)?)_pz\.mp4$", b)
    if m:
        for f in PHOTOS.glob(m.group(1) + ".*"):
            return str(f)
    return path


def main() -> int:
    wm = WikimediaClient()
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[2]
    used = set()
    for i in range(v3.clips.numItems):
        try:
            used.add(md5f(source_for(v3.clips[i].projectItem.getMediaPath())))
        except Exception:
            pass
    used.discard(None)
    tmp = Path(tempfile.mkdtemp())
    chosen = None
    for q in QUERIES:
        try:
            hits = wm.search_images(q, limit=15, min_width=1000)
        except Exception:
            hits = []
        for j, hit in enumerate(hits):
            o = tmp / f"c_{j}.jpg"
            try:
                wm.download(hit, o); h = md5f(o)
            except Exception:
                continue
            if h and h not in used:
                chosen = o; print(f"  фото: q='{q}'"); break
        if chosen:
            break
    if not chosen:
        print("  ✗ не нашёл глобально-уникального фото"); return 1
    pub = PHOTOS / f"{SID}_p4.jpg"; shutil.copy(chosen, pub)
    frames = max(45, round(DUR * 30))
    props = REMOTION / f"_pz_{SID}_p4.json"
    props.write_text(json.dumps({"img": f"photos/{SID}_p4.jpg", "dir": "in",
                                 "durationInFrames": int(frames)}), encoding="utf-8")
    outp = OUT / f"{SID}_p4_pz.mp4"
    r = subprocess.run(f'npx remotion render PhotoZoom "{os.path.relpath(outp, REMOTION)}" '
                       f'--props="{os.path.relpath(props, REMOTION)}" --codec=h264 --muted --log=error',
                       cwd=str(REMOTION), shell=True, capture_output=True, text=True)
    props.unlink(missing_ok=True)
    if r.returncode != 0:
        print("  ✗ render:", (r.stderr or "")[-150:]); return 1
    item = T.import_media(outp)
    T.place_clip(v3, item, START, overwrite=True)
    pymiere.objects.app.project.save()
    print(f"  ✓ idx={IDX} {SID} → {outp.name}; сохранено")
    return 0


if __name__ == "__main__":
    sys.exit(main())
