"""Точечно: дать Беляеву настоящий портрет + разнообразить фото эксперимента,
разложить на scene_253/254/274 с ротацией (без повтора подряд). Достоверность + анти-дубль."""
import hashlib, json, os, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
from services.stocks.wikipedia_photo import WikipediaPhotoClient
from services.stocks.wikimedia import WikimediaClient

PROJECT = ROOT / "projects" / "2026-08-18_aysberg-evolyutsii-temnaya-i-zapretnaya-storona-evolyutsii-o"
OUT = PROJECT / "assets" / "photozoom"
PUB = ROOT / "remotion" / "public" / "photos"
POR = PROJECT / "assets" / "portraits"
REMOTION = ROOT / "remotion"
tps = 254016000000
SCENES = ["scene_253", "scene_254", "scene_274"]

WIKI_TRY = ["Dmitry K. Belyayev", "Dmitri Belyayev", "Dmitri Belyaev (geneticist)"]
WM_TRY = ["Dmitri Belyaev geneticist portrait", "Belyaev domesticated fox experiment",
          "tame silver fox Novosibirsk", "Lyudmila Trut domesticated fox"]


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
    return outp if r.returncode == 0 else None


def main() -> int:
    wp = WikipediaPhotoClient(); wm = WikimediaClient()
    photos = []; seen = set()
    # портрет Беляева — приоритет первым в ротации
    for i, w in enumerate(WIKI_TRY):
        o = POR / f"bel_wiki_{i}.jpg"
        try:
            if wp.download_photo(w, o) and o.stat().st_size > 5000:
                h = md5f(o)
                if h not in seen: seen.add(h); photos.append(o); print(f"  wiki ✓ {w}"); break
        except Exception as e: print(f"  wiki ✗ {w}: {str(e)[:40]}")
    n_portrait = len(photos)
    for i, q in enumerate(WM_TRY):
        o = POR / f"bel_wm_{i}.jpg"
        try:
            if wm.search_and_download(q, o) and o.stat().st_size > 5000:
                h = md5f(o)
                if h not in seen: seen.add(h); photos.append(o); print(f"  wm ✓ {q}")
        except Exception as e: print(f"  wm ✗ {q}: {str(e)[:40]}")
    # добавим уже найденное ранее фото Трут с лисой, если есть
    old = POR / "belyaev_2.jpg"
    if old.exists() and md5f(old) not in seen:
        seen.add(md5f(old)); photos.append(old)
    print(f"итого фото: {len(photos)} (портрет: {n_portrait})")
    if not photos:
        print("нет фото — выход"); return 1

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
    clip_at = {}
    for i in range(v3.clips.numItems):
        c = v3.clips[i]; sid = scene_at(cstart(c))
        if sid and sid not in clip_at: clip_at[sid] = (i, max(1.5, cend(c) - cstart(c)))

    done = 0
    for k, sid in enumerate(SCENES):
        info = clip_at.get(sid)
        if not info: print(f"  ✗ {sid} слот нет"); continue
        img = photos[k % len(photos)]  # ротация: 253=портрет,254=след,274=след
        outp = render_pz(f"{sid}_bel", img, max(45, round(info[1] * 30)), "in" if k % 2 else "out")
        if not outp: print(f"  ✗ render {sid}"); continue
        try:
            v3.clips[info[0]].projectItem.changeMediaPath(str(outp.resolve()), True)
            done += 1; print(f"  ✓ {sid} ← {img.name}")
        except Exception as e: print(f"  ✗ swap {sid}: {str(e)[:50]}")
    pymiere.objects.app.project.save()
    print(f"\nготово: {done}/3; проект сохранён")
    return 0


if __name__ == "__main__":
    sys.exit(main())
