"""Скан живого таймлайна: какие медиа на V3 (тело) повторяются >1 раза.
Печатает группы повторов с временами и scene_id, чтобы точечно заменить."""
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pymiere


def mmss(t):
    return f"{int(t)//60:02d}:{int(t)%60:02d}"


def main() -> int:
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[2]
    tps = 254016000000  # ticks per second (Premiere)
    groups = defaultdict(list)
    for i in range(v3.clips.numItems):
        c = v3.clips[i]
        try:
            path = c.projectItem.getMediaPath()
        except Exception:
            path = "?"
        base = os.path.basename(path)
        start = c.start.seconds if hasattr(c.start, "seconds") else float(c.start.ticks) / tps
        groups[base].append((start, c.name))
    reps = {k: v for k, v in groups.items() if len(v) > 1 and k not in ("", "?")}
    print(f"всего клипов V3: {v3.clips.numItems} | уникальных медиа: {len(groups)} | ПОВТОРОВ: {len(reps)}\n")
    for base, items in sorted(reps.items(), key=lambda kv: -len(kv[1])):
        items.sort()
        times = ", ".join(f"{mmss(s)}({n})" for s, n in items)
        print(f"×{len(items)}  {base}")
        print(f"      {times}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
