"""Честный детектор ВИЗУАЛЬНЫХ повторов на V3: за каждым scene_XXX_pz.mp4 стоит
исходное фото remotion/public/photos/scene_XXX.* — хешируем ИСХОДНИК (а не рендер),
чтобы поймать одинаковые картинки под разными именами (портреты/Кичжондон крутятся).
Для НЕ-pz клипов хешируем сам медиа-файл."""
import hashlib
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere

PHOTOS = ROOT / "remotion" / "public" / "photos"
tps = 254016000000


def mmss(t):
    return f"{int(t)//60:02d}:{int(t)%60:02d}"


def h(p):
    try:
        return hashlib.md5(Path(p).read_bytes()).hexdigest()[:12]
    except Exception:
        return None


def source_for(path):
    """pz-клип → его исходное фото public/photos/scene_XXX.*; иначе сам файл."""
    b = os.path.basename(path)
    # берём ТОЧНЫЙ стем перед _pz (scene_015 / scene_015_d / scene_015_p2)
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
        try:
            path = c.projectItem.getMediaPath()
        except Exception:
            continue
        src = source_for(path)
        digest = h(src)
        if not digest:
            continue
        start = c.start.seconds if hasattr(c.start, "seconds") else float(c.start.ticks) / tps
        groups[digest].append((start, i, os.path.basename(src)))
    reps = {k: v for k, v in groups.items() if len(v) > 1}
    total_dupe_clips = sum(len(v) for v in reps.values())
    print(f"клипов V3: {v3.clips.numItems} | уник.картинок: {len(groups)} | "
          f"групп-повторов: {len(reps)} | клипов в повторах: {total_dupe_clips}\n")
    for digest, items in sorted(reps.items(), key=lambda kv: -len(kv[1])):
        items.sort()
        src = items[0][2]
        tc = ", ".join(f"{mmss(s)}[{i}]" for s, i, _ in items)
        print(f"x{len(items)}  {src}")
        print(f"      {tc}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
