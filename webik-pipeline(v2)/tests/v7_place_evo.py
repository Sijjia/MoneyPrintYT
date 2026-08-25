"""Ставит готовые сцен-вставки НА V7 (overlay-слой, видно что добавлено), ровно
по длине сцены, полное перекрытие (hard cut, без фейдов). ТЕЛО V3 НЕ трогаем.
Идемпотентно: чистит V7 и раскладывает заново из v7_inserts/.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pymiere
from pymiere.wrappers import time_from_seconds
from services.premiere_template.timeline_ops import import_media

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-08-18_aysberg-evolyutsii-temnaya-i-zapretnaya-storona-evolyutsii-o"
OUT = (PROJECT / "assets" / "v7_inserts").resolve()
V7 = 6


def main() -> int:
    ins = json.loads((PROJECT / "v7_inserts.json").read_text(encoding="utf-8"))["inserts"]
    seq = pymiere.objects.app.project.activeSequence
    v7 = seq.videoTracks[V7]
    # чистим только V7 (наш слой)
    for cl in reversed(list(v7.clips)):
        cl.remove(False, False)
    placed = 0
    for c in ins:
        sid = c["scene_id"]; at = float(c["start"]); start = int(at)
        mov = OUT / f"v7_{sid}_{start}_6.mov"
        if not (mov.exists() and mov.stat().st_size > 5000):
            continue
        item = import_media(mov)
        if item is None:
            print(f"    import упал: {mov.name}"); continue
        try:
            v7.overwriteClip(item, time_from_seconds(round(at, 2)))
            placed += 1
            print(f"    ✓ V7 {start//60:02d}:{start%60:02d} {sid}")
        except Exception as e:
            print(f"    overwrite упал {sid}: {str(e)[:90]}")
    pymiere.objects.app.project.save()
    print(f"\nПОСТАВЛЕНО на V7: {placed}/{len(ins)} (тело V3 не тронуто), проект сохранён")
    return 0


if __name__ == "__main__":
    sys.exit(main())
