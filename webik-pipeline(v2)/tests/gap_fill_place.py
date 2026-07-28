"""Врезает готовые gapfill_*.mov в чёрные дыры тела V3 (overwrite, жёсткий стык).
Идемпотентно: ставит только те дыры, для которых есть .mov. Повторный запуск
после докачки остальных доставит их.
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
OUT = (PROJECT / "assets" / "cutaways").resolve()
BODY_TRACK = 2  # V3


def main() -> int:
    gaps = json.loads((PROJECT / "gaps.json").read_text(encoding="utf-8"))
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[BODY_TRACK]
    placed = skipped = 0
    for g in gaps:
        sid = g["scene_id"]; at = float(g["start"])
        mov = OUT / f"gapfill_{sid}_{int(at)}.mov"
        if not (mov.exists() and mov.stat().st_size > 5000):
            skipped += 1; continue
        item = import_media(mov)
        if item is None:
            print(f"    import упал: {mov.name}"); continue
        try:
            v3.overwriteClip(item, time_from_seconds(round(at, 2)))
            placed += 1
            print(f"    ✓ дыра {int(at)//60:02d}:{int(at)%60:02d} {sid} ({g['dur']:.1f}с)")
        except Exception as e:
            print(f"    overwrite упал {sid}: {str(e)[:100]}")
    pymiere.objects.app.project.save()
    print(f"\nЗАПОЛНЕНО дыр: {placed} (нет .mov ещё: {skipped}), проект сохранён")
    return 0


if __name__ == "__main__":
    sys.exit(main())
