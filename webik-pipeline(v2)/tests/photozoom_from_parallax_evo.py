"""parallax-3D → чистый PhotoZoom для «Айсберг эволюции» (правка Айдара).
Матчим по МАНИФЕСТУ (source=wikimedia/wikipedia-person = архив-фото) + ВРЕМЕНИ alignment
(не по имени клипа — оно ненадёжно, напр. scene_318 на 0:00). Для каждой архив-сцены:
её слот на V3 по времени → PhotoZoom из assets/images/scene_XXX_wm.* → changeMediaPath.
Заодно чинит первую сцену (scene_001) на 0:00."""
import json, os, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere

PROJECT = ROOT / "projects" / "2026-08-18_aysberg-evolyutsii-temnaya-i-zapretnaya-storona-evolyutsii-o"
IMAGES = PROJECT / "assets" / "images"
OUT = PROJECT / "assets" / "photozoom"
PUB = ROOT / "remotion" / "public" / "photos"
REMOTION = ROOT / "remotion"
tps = 254016000000
OUT.mkdir(parents=True, exist_ok=True); PUB.mkdir(parents=True, exist_ok=True)
ARCHIVE_SOURCES = {"wikimedia", "wikipedia-person"}


def cstart(c): return c.start.seconds if hasattr(c.start, "seconds") else float(c.start.ticks) / tps
def cend(c): return c.end.seconds if hasattr(c.end, "seconds") else float(c.end.ticks) / tps


def find_src(sid):
    for ext in (".jpg", ".png", ".jpeg", ".webp"):
        p = IMAGES / f"{sid}_wm{ext}"
        if p.exists():
            return p
    hits = list(IMAGES.glob(f"{sid}_*.jpg")) + list(IMAGES.glob(f"{sid}.*"))
    return hits[0] if hits else None


def render_pz(sid, img, frames, direction):
    suffix = img.suffix or ".jpg"
    pub = PUB / f"{sid}_pz{suffix}"; shutil.copy(img, pub)
    props = REMOTION / f"_pz_{sid}.json"
    props.write_text(json.dumps({"img": f"photos/{sid}_pz{suffix}", "dir": direction,
                                 "durationInFrames": int(frames)}), encoding="utf-8")
    outp = OUT / f"{sid}_pz.mp4"
    r = subprocess.run(f'npx remotion render PhotoZoom "{os.path.relpath(outp, REMOTION)}" '
                       f'--props="{os.path.relpath(props, REMOTION)}" --codec=h264 --muted --log=error',
                       cwd=str(REMOTION), shell=True, capture_output=True, text=True)
    props.unlink(missing_ok=True)
    if r.returncode != 0:
        print("    render:", (r.stderr or "")[-140:]); return None
    return outp


def main() -> int:
    man = json.loads((PROJECT / "assets" / "images" / "manifest.json").read_text(encoding="utf-8"))
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    arch = {sid for sid, v in man.items() if v.get("source") in ARCHIVE_SOURCES}
    print(f"архив-сцен (wikimedia/person): {len(arch)}")
    ivals = sorted(((al[s]["start"], al[s]["end"], s) for s in al), key=lambda x: x[0])

    def scene_at(t):
        best = None
        for st, en, s in ivals:
            if st - 0.05 <= t < en + 0.05:
                return s
            if st <= t:
                best = s
        return best

    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[2]
    # слот V3 → сцена по времени; берём клипы, чья сцена = архив
    jobs = []
    seen = set()
    for i in range(v3.clips.numItems):
        c = v3.clips[i]
        s = cstart(c); e = cend(c)
        sid = scene_at(s)
        if sid in arch and sid not in seen:
            seen.add(sid)
            jobs.append((i, sid, max(1.5, e - s)))
    print(f"слотов под свап: {len(jobs)}")

    done = fail = 0
    for k, (idx, sid, dur) in enumerate(jobs):
        src = find_src(sid)
        if not src:
            fail += 1; print(f"  ✗ {sid}: исходник не найден"); continue
        frames = max(45, round(dur * 30))
        outp = render_pz(sid, src, frames, "in" if k % 2 else "out")
        if not outp:
            fail += 1; continue
        try:
            v3.clips[idx].projectItem.changeMediaPath(str(outp.resolve()), True)
            done += 1
            if done % 15 == 0:
                print(f"  ...{done}/{len(jobs)} свапнуто")
        except Exception as ex:
            fail += 1; print(f"  ✗ swap {sid}: {str(ex)[:70]}")
    pymiere.objects.app.project.save()
    print(f"\nготово: PhotoZoom {done}/{len(jobs)}, провал {fail}; проект сохранён")
    return 0


if __name__ == "__main__":
    sys.exit(main())
