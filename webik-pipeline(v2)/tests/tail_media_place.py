"""Перезаписывает медиа тела V3 для хвоста (сцены 177-190) на новый архив
(assets/tail_media/{scene}_{start}.mov), overwrite по началу сцены. Только эти
сцены, остальное не трогаем. Бэкап проекта делается ДО запуска (снаружи).
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pymiere
from pymiere.wrappers import time_from_seconds
from services.premiere_template.timeline_ops import import_media

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-"
OUT = (PROJECT / "assets" / "tail_media").resolve()
LO, HI = 177, 190


def main() -> int:
    sm = json.loads((PROJECT / "scene_map.json").read_text(encoding="utf-8"))
    targets = {}
    for s in sm:
        m = re.match(r"scene_(\d+)", s["scene_id"])
        if m and LO <= int(m.group(1)) <= HI:
            targets[s["scene_id"]] = s
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[2]
    placed = 0
    for sid, s in sorted(targets.items(), key=lambda kv: kv[1]["start"]):
        start = int(float(s["start"]))
        mov = OUT / f"{sid}_{start}.mov"
        if not (mov.exists() and mov.stat().st_size > 5000):
            continue
        item = import_media(mov)
        if item is None:
            print(f"    import упал: {mov.name}"); continue
        try:
            v3.overwriteClip(item, time_from_seconds(round(float(s["start"]), 2)))
            placed += 1
            print(f"    ✓ {sid} @ {start//60}:{start%60:02d}")
        except Exception as e:
            print(f"    overwrite упал {sid}: {str(e)[:90]}")
    pymiere.objects.app.project.save()
    print(f"\nперезаписано медиа V3: {placed}/{len(targets)}, проект сохранён")
    return 0


if __name__ == "__main__":
    sys.exit(main())
