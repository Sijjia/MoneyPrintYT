"""Устранить визуальные повторы на V3 (после пересборки): каждой группе одинаковых
картинок оставляем ПЕРВОЕ вхождение, остальным даём ДРУГОЕ фото по запросу сцены
(глобальный avoid-set по хешам). Wikimedia-стилл → PhotoZoom; если нет — Pexels-видео."""
import hashlib, json, os, re, shutil, subprocess, sys, tempfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
from services.stocks.wikimedia import WikimediaClient
from services.stocks.pexels_videos import PexelsVideosClient

PROJECT = ROOT / "projects" / "2026-08-18_aysberg-evolyutsii-temnaya-i-zapretnaya-storona-evolyutsii-o"
PHOTOS = ROOT / "remotion" / "public" / "photos"
OUT = PROJECT / "assets" / "relmedia"
VID = PROJECT / "assets" / "video_stock"
REMOTION = ROOT / "remotion"
tps = 254016000000
EXTRA = ["prehistoric evolution", "ancient fossil museum", "DNA genetics laboratory", "dark nature macro",
         "human skull anthropology", "old scientific archive", "wildlife animal", "microscope cells"]
for d in (OUT, VID, PHOTOS):
    d.mkdir(parents=True, exist_ok=True)


def md5(b): return hashlib.md5(b).hexdigest()[:12]
def md5f(p):
    try: return md5(Path(p).read_bytes())
    except Exception: return None
def cstart(c): return c.start.seconds if hasattr(c.start, "seconds") else float(c.start.ticks) / tps
def cend(c): return c.end.seconds if hasattr(c.end, "seconds") else float(c.end.ticks) / tps


def source_for(path):
    b = os.path.basename(path)
    m = re.match(r"(scene_\d+)_(?:rz|mz)\.mp4$", b)
    if m:
        for f in PHOTOS.glob(m.group(1) + "_r0.*"): return str(f)
        return path
    m = re.match(r"(scene_\d+(?:_[a-z0-9]+)?)_pz\.mp4$", b)
    if m:
        for f in PHOTOS.glob(m.group(1) + ".*"): return str(f)
    return path


def render_pz(tag, img, frames, direction):
    suffix = Path(img).suffix or ".jpg"
    pub = PHOTOS / f"{tag}{suffix}"; shutil.copy(img, pub)
    props = REMOTION / f"_dd_{tag}.json"
    props.write_text(json.dumps({"img": f"photos/{tag}{suffix}", "dir": direction, "durationInFrames": int(frames)}), encoding="utf-8")
    outp = OUT / f"{tag}_pz.mp4"
    r = subprocess.run(f'npx remotion render PhotoZoom "{os.path.relpath(outp, REMOTION)}" '
                       f'--props="{os.path.relpath(props, REMOTION)}" --codec=h264 --muted --log=error',
                       cwd=str(REMOTION), shell=True, capture_output=True, text=True)
    props.unlink(missing_ok=True)
    return outp if r.returncode == 0 else None


def find_still(wm, queries, used, tmp, tag):
    for q in queries:
        if not q: continue
        try: hits = wm.search_images(q, limit=14, min_width=1000)
        except Exception: hits = []
        for j, hit in enumerate(hits):
            o = tmp / f"{tag}_{j}.jpg"
            try: wm.download(hit, o); h = md5f(o)
            except Exception: continue
            if h and h not in used: return o, h
    return None, None


def main() -> int:
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    by_id = {s["id"]: s for s in scenes}
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    ivals = sorted(((al[s]["start"], al[s]["end"], s) for s in al), key=lambda x: x[0])
    def scene_at(t):
        best = None
        for st, en, s in ivals:
            if st - 0.05 <= t < en + 0.05: return s
            if st <= t: best = s
        return best

    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[2]
    clips = []
    for i in range(v3.clips.numItems):
        c = v3.clips[i]
        try: h = md5f(source_for(c.projectItem.getMediaPath()))
        except Exception: h = None
        clips.append({"idx": i, "start": cstart(c), "end": cend(c), "hash": h})
    groups = defaultdict(list)
    for cl in clips:
        if cl["hash"]: groups[cl["hash"]].append(cl)
    used = set(groups.keys())
    targets = []
    for h, items in groups.items():
        if len(items) < 2: continue
        items.sort(key=lambda x: x["start"])
        targets += items[1:]
    targets.sort(key=lambda x: x["start"])
    print(f"групп-повторов: {sum(1 for v in groups.values() if len(v)>1)} | к замене: {len(targets)}")

    wm = WikimediaClient(); px = PexelsVideosClient(); tmp = Path(tempfile.mkdtemp())
    ok = fail = vid = 0
    for k, cl in enumerate(targets):
        idx = cl["idx"]; st = cl["start"]; dur = max(2.0, cl["end"] - cl["start"]); frames = max(60, round(dur * 30))
        sid = scene_at(st); s = by_id.get(sid, {}); vis = s.get("visual", {})
        queries = [vis.get("search_query"), vis.get("fallback_query")] + EXTRA
        tag = f"{sid}_dd{k}"
        img, h = find_still(wm, queries, used, tmp, tag)
        if img:
            outp = render_pz(tag, img, frames, "in" if k % 2 else "out")
            if outp:
                try:
                    v3.clips[idx].projectItem.changeMediaPath(str(outp.resolve()), True)
                    used.add(h); ok += 1; print(f"  ✓ {sid} @{int(st//60):02d}:{int(st%60):02d}"); continue
                except Exception as e: print(f"  ✗ swap {sid}: {str(e)[:50]}")
        # видео-фолбэк
        for q in [vis.get("search_query"), vis.get("fallback_query"), "nature dark"]:
            if not q: continue
            try:
                o = VID / f"{tag}.mp4"
                if px.search_and_download(q, o, index=(k % 3)) and o.stat().st_size > 20000:
                    hh = md5f(o)
                    if hh and hh not in used:
                        v3.clips[idx].projectItem.changeMediaPath(str(o.resolve()), True)
                        used.add(hh); vid += 1; print(f"  ✓ВИДЕО {sid}"); break
            except Exception: continue
        else:
            fail += 1; print(f"  ✗ {sid}: не нашёл уникум")
    pymiere.objects.app.project.save()
    print(f"\nдедуп: фото={ok} видео={vid} провал={fail}; проект сохранён")
    return 0


if __name__ == "__main__":
    sys.exit(main())
