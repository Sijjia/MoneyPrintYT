"""scene_019: поставить фото северокорейского школьника (по просьбе Айдара).
Fetch Wikimedia → PhotoZoom ровно в слот → import → overwrite на V3."""
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
tps = 254016000000
SID = "scene_019"
QUERIES = ["North Korean schoolchildren", "North Korea school students uniform",
           "Pyongyang schoolchildren", "North Korea children pioneers red scarf",
           "North Korea students Kim Il Sung"]


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
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    a = al[SID]; st0, en0 = a["start"], a["end"]
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[2]
    # avoid-set = хеши всех клипов; и найти клип scene_019 по времени
    used = set(); target = None
    for i in range(v3.clips.numItems):
        c = v3.clips[i]
        s = c.start.seconds if hasattr(c.start, "seconds") else float(c.start.ticks) / tps
        e = c.end.seconds if hasattr(c.end, "seconds") else float(c.end.ticks) / tps
        try:
            used.add(md5f(source_for(c.projectItem.getMediaPath())))
        except Exception:
            pass
        if s <= st0 + 0.3 and e >= en0 - 0.3 and (st0 - 0.5) <= s <= (st0 + 0.8):
            target = (i, s, e)
    used.discard(None)
    if not target:
        # fallback: ближайший по старту
        best = None
        for i in range(v3.clips.numItems):
            c = v3.clips[i]
            s = c.start.seconds if hasattr(c.start, "seconds") else float(c.start.ticks) / tps
            e = c.end.seconds if hasattr(c.end, "seconds") else float(c.end.ticks) / tps
            if best is None or abs(s - st0) < abs(best[1] - st0):
                best = (i, s, e)
        target = best
    idx, s, e = target
    dur = max(1.5, e - s); frames = max(45, round(dur * 30))
    print(f"цель: idx={idx} {s:.1f}-{e:.1f} ({dur:.1f}с)")

    wm = WikimediaClient(); tmp = Path(tempfile.mkdtemp()); chosen = None
    for q in QUERIES:
        try:
            hits = wm.search_images(q, limit=15, min_width=900)
        except Exception:
            hits = []
        for j, hit in enumerate(hits):
            o = tmp / f"c_{j}.jpg"
            try:
                wm.download(hit, o); h = md5f(o)
            except Exception:
                continue
            if h and h not in used:
                chosen = o; print(f"фото: q='{q}'"); break
        if chosen:
            break
    if not chosen:
        print("✗ не нашёл фото школьника"); return 1
    pub = PHOTOS / f"{SID}_sc.jpg"; shutil.copy(chosen, pub)
    props = REMOTION / f"_pz_{SID}_sc.json"
    props.write_text(json.dumps({"img": f"photos/{SID}_sc.jpg", "dir": "in",
                                 "durationInFrames": int(frames)}), encoding="utf-8")
    outp = OUT / f"{SID}_sc_pz.mp4"
    r = subprocess.run(f'npx remotion render PhotoZoom "{os.path.relpath(outp, REMOTION)}" '
                       f'--props="{os.path.relpath(props, REMOTION)}" --codec=h264 --muted --log=error',
                       cwd=str(REMOTION), shell=True, capture_output=True, text=True)
    props.unlink(missing_ok=True)
    if r.returncode != 0:
        print("✗ render:", (r.stderr or "")[-160:]); return 1
    item = T.import_media(outp)
    if item is None:
        print("✗ import"); return 1
    T.place_clip(v3, item, s, overwrite=True)
    pymiere.objects.app.project.save()
    print(f"✓ scene_019 → фото школьника ({outp.name}); проект сохранён")
    return 0


if __name__ == "__main__":
    sys.exit(main())
