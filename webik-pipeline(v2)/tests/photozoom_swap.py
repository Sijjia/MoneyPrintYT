"""Подмена фото-сцен на плавный PhotoZoom (assets/photozoom/scene_XXX_pz.mp4) на V3
по имени клипа. Запускать после photozoom_render.py.
"""
import glob
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pymiere
from services.premiere_template import timeline_ops  # noqa: F401

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-"
PZ = PROJECT / "assets" / "photozoom"


def main() -> int:
    clips = {}
    for f in glob.glob(str(PZ / "scene_*_pz.mp4")):
        m = re.match(r"(scene_\d+)_pz", os.path.basename(f))
        if m:
            clips[m.group(1)] = f
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[2]
    byname = {}
    for i in range(v3.clips.numItems):
        c = v3.clips[i]
        m = re.match(r"(scene_\d+)", c.name)
        if m:
            byname.setdefault(m.group(1), c)
    sw, miss = 0, []
    for sid, f in sorted(clips.items()):
        c = byname.get(sid)
        if c is None:
            miss.append(sid); continue
        try:
            c.projectItem.changeMediaPath(str(Path(f).resolve()), True)
            sw += 1
        except Exception as e:
            print(f"  {sid}: {e}")
    pymiere.objects.app.project.save()
    print(f"плавный зум наложен {sw}/{len(clips)}; не найдены: {miss}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
