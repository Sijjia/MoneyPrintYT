"""Повторное наложение реальных медиа на V3 после пересборки.
Для каждой сцены с готовым реальным клипом (assets/archive_clips|archive_stock,
самый свежий вариант _real/_arch/_fig/_yt) находит клип на V3 по имени scene_XXX
и делает changeMediaPath (позиция-независимо, тайминг из нового таймлайна).
"""
import glob
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pymiere
from services.premiere_template import timeline_ops  # noqa: F401 (patch __del__)

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-"


def newest_per_scene() -> dict:
    cands = {}
    for d in ("assets/archive_clips", "assets/archive_stock"):
        for f in glob.glob(str(PROJECT / d / "scene_*.mp4")):
            m = re.match(r"scene_(\d+)_(real|arch|fig|yt)", Path(f).name)
            if not m:
                continue
            sid = "scene_" + m.group(1)
            mt = os.path.getmtime(f)
            if sid not in cands or mt > cands[sid][1]:
                cands[sid] = (f, mt)
    return {sid: v[0] for sid, v in cands.items()}


def main() -> int:
    media = newest_per_scene()
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[2]
    # индекс клипов V3 по имени scene_XXX
    byname = {}
    for i in range(v3.clips.numItems):
        c = v3.clips[i]
        m = re.match(r"(scene_\d+)", c.name)
        if m:
            byname.setdefault(m.group(1), c)
    swapped, missing = 0, []
    for sid, f in sorted(media.items()):
        clip = byname.get(sid)
        if clip is None:
            missing.append(sid); continue
        try:
            clip.projectItem.changeMediaPath(str(Path(f).resolve()), True)
            swapped += 1
        except Exception as e:
            print(f"  {sid}: упал {e}")
    pymiere.objects.app.project.save()
    print(f"реальных медиа наложено {swapped}/{len(media)}; не найдены клипы: {missing}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
