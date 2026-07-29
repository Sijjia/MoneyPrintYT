"""Врезает отрендеренные фоны тем (topic_bg/{scene}_{start}_bg.mp4) в дыры на
началах тем (V3), overwrite. Плашка темы (V4) остаётся поверх.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pymiere
from pymiere.wrappers import time_from_seconds
from services.premiere_template.timeline_ops import import_media

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-"
OUT = (PROJECT / "assets" / "topic_bg").resolve()


def main() -> int:
    gaps = json.loads((PROJECT / "topic_gaps.json").read_text(encoding="utf-8"))
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[2]
    placed = 0
    for g in gaps:
        sid = g["scene_id"]; at = float(g["start"]); start = int(at)
        mov = OUT / f"{sid}_{start}_bg.mp4"
        if not (mov.exists() and mov.stat().st_size > 5000):
            print(f"    нет фона: {mov.name}"); continue
        item = import_media(mov)
        if item is None:
            print(f"    import упал: {mov.name}"); continue
        try:
            v3.overwriteClip(item, time_from_seconds(round(at, 2)))
            placed += 1
            print(f"    ✓ тема {start//60:02d}:{start%60:02d} {sid}")
        except Exception as e:
            print(f"    overwrite упал {sid}: {str(e)[:100]}")
    pymiere.objects.app.project.save()
    # финальная проверка дыр
    clips = sorted([(c.start.seconds, c.end.seconds) for c in v3.clips])
    big = [(clips[i-1][1], clips[i][0]) for i in range(1, len(clips)) if clips[i][0]-clips[i-1][1] > 2.5]
    print(f"\nВРЕЗАНО фонов тем: {placed}, больших дыр в теле ОСТАЛОСЬ: {len(big)}")
    for a, b in big:
        print(f"  {int(a)//60:02d}:{int(a)%60:02d} ({b-a:.1f}с)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
