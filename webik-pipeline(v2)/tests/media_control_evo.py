"""Медиа-контроль «Айсберг эволюции», одна Premiere-сессия:
  1) Портреты названных учёных (Паабо, Беляев) на их сцены — реальные фото, ротация.
  2) Фикс 2 визуальных повторов (2-е вхождение → другое тематическое фото).
  3) Добить scene_080 (провал импорта на сборке) — тематическое фото.
Всё: fetch → PhotoZoom ровно в слот → changeMediaPath по времени сцены. avoid-set по хешам."""
import hashlib, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
from services.stocks.wikipedia_photo import WikipediaPhotoClient
from services.stocks.wikimedia import WikimediaClient

PROJECT = ROOT / "projects" / "2026-08-18_aysberg-evolyutsii-temnaya-i-zapretnaya-storona-evolyutsii-o"
IMAGES = PROJECT / "assets" / "images"
OUT = PROJECT / "assets" / "photozoom"
PUB = ROOT / "remotion" / "public" / "photos"
POR = PROJECT / "assets" / "portraits"
REMOTION = ROOT / "remotion"
tps = 254016000000
for d in (OUT, PUB, POR): d.mkdir(parents=True, exist_ok=True)

PEOPLE = [
    {"key": "paabo", "scenes": ["scene_019", "scene_020"],
     "wiki": "Svante Pääbo", "wm": ["Svante Pääbo", "Svante Paabo Max Planck"]},
    {"key": "belyaev", "scenes": ["scene_253", "scene_254", "scene_274"],
     "wiki": "Dmitri Belyaev (zoologist)",
     "wm": ["Dmitri Belyaev geneticist", "Lyudmila Trut fox", "domesticated silver fox Novosibirsk"]},
]
# фикс-слоты: (scene_id ЦЕЛЕВОЙ сцены на 2-м вхождении / провал), запросы берём из scenes.json
FIX_SCENES = ["scene_080"]  # провал импорта
# 2-е вхождения повторов адресуем по времени ниже


def md5f(p):
    try: return hashlib.md5(Path(p).read_bytes()).hexdigest()[:12]
    except Exception: return None
def cstart(c): return c.start.seconds if hasattr(c.start, "seconds") else float(c.start.ticks) / tps
def cend(c): return c.end.seconds if hasattr(c.end, "seconds") else float(c.end.ticks) / tps


def render_pz(tag, img, frames, direction):
    suffix = Path(img).suffix or ".jpg"
    pub = PUB / f"{tag}{suffix}"; shutil.copy(img, pub)
    props = REMOTION / f"_pz_{tag}.json"
    props.write_text(json.dumps({"img": f"photos/{tag}{suffix}", "dir": direction,
                                 "durationInFrames": int(frames)}), encoding="utf-8")
    outp = OUT / f"{tag}_pz.mp4"
    r = subprocess.run(f'npx remotion render PhotoZoom "{os.path.relpath(outp, REMOTION)}" '
                       f'--props="{os.path.relpath(props, REMOTION)}" --codec=h264 --muted --log=error',
                       cwd=str(REMOTION), shell=True, capture_output=True, text=True)
    props.unlink(missing_ok=True)
    if r.returncode != 0:
        print("    render:", (r.stderr or "")[-140:]); return None
    return outp


def fetch_person(p):
    wp = WikipediaPhotoClient(); wm = WikimediaClient(); photos = []
    o = POR / f"{p['key']}_0.jpg"
    try:
        if wp.download_photo(p["wiki"], o) and o.stat().st_size > 5000: photos.append(o)
    except Exception as e: print(f"  wiki {p['key']}: {str(e)[:40]}")
    for i, q in enumerate(p["wm"], 1):
        o = POR / f"{p['key']}_{i}.jpg"
        try:
            if wm.search_and_download(q, o) and o.stat().st_size > 5000: photos.append(o)
        except Exception as e: print(f"  wm {p['key']} '{q}': {str(e)[:40]}")
    # дедуп по хешу
    seen = {}; uniq = []
    for f in photos:
        h = md5f(f)
        if h and h not in seen: seen[h] = 1; uniq.append(f)
    print(f"  {p['key']}: {len(uniq)} уник.фото")
    return uniq


def find_unique_still(wm, queries, used, tmp, tag):
    for q in queries:
        if not q: continue
        try: hits = wm.search_images(q, limit=12, min_width=900)
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
    # индекс: слот по времени → (idx, start, end); и обратная карта scene→idx
    clip_at = {}   # scene_id -> (idx, dur)
    used = set()
    for i in range(v3.clips.numItems):
        c = v3.clips[i]; s = cstart(c); e = cend(c)
        try: used.add(md5f(_src_for(c.projectItem.getMediaPath())))
        except Exception: pass
        sid = scene_at(s)
        if sid and sid not in clip_at:
            clip_at[sid] = (i, max(1.5, e - s))
    used.discard(None)

    def swap_scene(sid, media_path):
        info = clip_at.get(sid)
        if not info: print(f"  ✗ {sid}: слот не найден"); return False
        idx = info[0]
        try:
            v3.clips[idx].projectItem.changeMediaPath(str(Path(media_path).resolve()), True); return True
        except Exception as e: print(f"  ✗ swap {sid}: {str(e)[:60]}"); return False

    wm = WikimediaClient(); tmp = Path(tempfile.mkdtemp())
    done = 0

    # 1) портреты
    for p in PEOPLE:
        photos = fetch_person(p)
        if not photos: continue
        for k, sid in enumerate(p["scenes"]):
            info = clip_at.get(sid)
            if not info: print(f"  ✗ {sid} слот нет"); continue
            img = photos[k % len(photos)]
            outp = render_pz(f"{sid}_por", img, max(45, round(info[1] * 30)), "in" if k % 2 else "out")
            if outp and swap_scene(sid, outp):
                done += 1; print(f"  ✓ портрет {p['key']} → {sid}")

    # 2) повторы: 2-е вхождения по времени (scene_041 @28:13, scene_117 @24:04)
    for t in (1693.0, 1444.0):
        sid = scene_at(t)
        s = by_id.get(sid, {}); vis = s.get("visual", {})
        img, h = find_unique_still(wm, [vis.get("search_query"), vis.get("fallback_query"),
                                        (s.get("voiceover") or "")[:60]], used, tmp, f"rep_{int(t)}")
        if img:
            info = clip_at.get(sid)
            if info:
                outp = render_pz(f"{sid}_dedup", img, max(45, round(info[1] * 30)), "out")
                if outp and swap_scene(sid, outp): used.add(h); done += 1; print(f"  ✓ дедуп {sid} @{int(t//60):02d}:{int(t%60):02d}")
        else:
            print(f"  ✗ дедуп {sid}: нет уник.фото")

    # 3) scene_080
    for sid in FIX_SCENES:
        s = by_id.get(sid, {}); vis = s.get("visual", {})
        img, h = find_unique_still(wm, [vis.get("search_query"), vis.get("fallback_query"),
                                        (s.get("voiceover") or "")[:60]], used, tmp, sid)
        if img:
            info = clip_at.get(sid)
            if info:
                outp = render_pz(f"{sid}_fix", img, max(45, round(info[1] * 30)), "in")
                if outp and swap_scene(sid, outp): used.add(h); done += 1; print(f"  ✓ фикс {sid}")
        else:
            print(f"  ✗ {sid}: нет фото")

    pymiere.objects.app.project.save()
    print(f"\nготово: {done} правок; проект сохранён")
    return 0


import re
def _src_for(path):
    b = os.path.basename(path)
    m = re.match(r"(scene_\d+(?:_[a-z0-9]+)?)_pz\.mp4$", b)
    if m:
        for f in PUB.glob(m.group(1) + ".*"): return str(f)
    return path


if __name__ == "__main__":
    sys.exit(main())
