"""Кладёт bespoke кино-сцены (assets/cine/*.mov) на V8 (idx7) по времени из cine_scenes.json."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
from pymiere.wrappers import time_from_seconds
from services.premiere_template.timeline_ops import import_media, place_clip

PROJECT = ROOT / "projects" / "2026-08-18_aysberg-evolyutsii-temnaya-i-zapretnaya-storona-evolyutsii-o"
CINE = PROJECT / "assets" / "cine"
V8_IDX = 7


def main() -> int:
    scenes = json.loads((PROJECT / "cine_scenes.json").read_text(encoding="utf-8"))["scenes"]
    seq = pymiere.objects.app.project.activeSequence
    v8 = seq.videoTracks[V8_IDX]
    placed = miss = 0
    for s in scenes:
        mov = CINE / f"{s['id']}.mov"
        if not mov.exists() or mov.stat().st_size < 10000:
            print(f"  ✗ {s['id']}: нет .mov"); miss += 1; continue
        item = import_media(mov)
        if item is None:
            print(f"  ✗ {s['id']}: import не удался"); miss += 1; continue
        try:
            place_clip(v8, item, float(s["start"]), overwrite=True)
            placed += 1
            print(f"  ✓ {s['id']} @ {int(s['start']//60):02d}:{int(s['start']%60):02d}")
        except Exception as e:
            print(f"  ✗ {s['id']}: {str(e)[:70]}"); miss += 1
    pymiere.objects.app.project.save()
    print(f"\nкино-сцен на V8: {placed}/{len(scenes)} (miss {miss}); проект сохранён")
    return 0


if __name__ == "__main__":
    sys.exit(main())
