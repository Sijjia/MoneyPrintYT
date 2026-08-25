"""Детектор ВИЗУАЛЬНЫХ повторов на V3 для «Айсберг эволюции».
Для PhotoZoom-клипов (scene_XXX_pz.mp4) хешируем исходное фото public/photos/scene_XXX_pz.*;
для видео (_trimmed/scene_NNN.mp4) хешим сам файл. Группируем по контенту."""
import hashlib, os, re, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere

PHOTOS = ROOT / "remotion" / "public" / "photos"
tps = 254016000000


def mmss(t): return f"{int(t)//60:02d}:{int(t)%60:02d}"
def cstart(c): return c.start.seconds if hasattr(c.start, "seconds") else float(c.start.ticks) / tps


def h(p):
    try: return hashlib.md5(Path(p).read_bytes()).hexdigest()[:12]
    except Exception: return None


def source_for(path):
    b = os.path.basename(path)
    # пересобранное медиа: {sid}_rz.mp4 / {sid}_mz.mp4 → исходник public/photos/{sid}_r0.*
    m = re.match(r"(scene_\d+)_(?:rz|mz)\.mp4$", b)
    if m:
        for f in PHOTOS.glob(m.group(1) + "_r0.*"):
            return str(f)
        return path
    m = re.match(r"(scene_\d+(?:_[a-z0-9]+)?)_pz\.mp4$", b)
    if m:
        for f in PHOTOS.glob(m.group(1) + ".*"):
            return str(f)
    return path


def main() -> int:
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[2]
    groups = defaultdict(list)
    for i in range(v3.clips.numItems):
        c = v3.clips[i]
        try: path = c.projectItem.getMediaPath()
        except Exception: continue
        digest = h(source_for(path))
        if digest:
            groups[digest].append((cstart(c), i, os.path.basename(source_for(path))))
    reps = {k: v for k, v in groups.items() if len(v) > 1}
    print(f"клипов V3: {v3.clips.numItems} | уник.контента: {len(groups)} | групп-повторов: {len(reps)} | "
          f"клипов в повторах: {sum(len(v) for v in reps.values())}\n")
    for d, items in sorted(reps.items(), key=lambda kv: -len(kv[1])):
        items.sort()
        print(f"x{len(items)}  {items[0][2]}")
        print("      " + ", ".join(f"{mmss(s)}[{i}]" for s, i, _ in items) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
