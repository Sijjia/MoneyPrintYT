"""Полная укладка графики: быстрые оверлеи + кино-сцены, с дедупом.
Кино-сцена (полноэкранная, ~30с) поглощает быстрые оверлеи внутри своего окна.
Запуск:
    PYTHONUTF8=1 ../webik-pipeline/.venv/Scripts/python.exe tests/place_all_graphics.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pymiere

from services.premiere.overlay_placer import place_overlays

PROJECT = Path("projects/2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-")
OVERLAY_TRACK = 7  # V8


def main():
    quick = json.loads((PROJECT / "overlays_rendered.json").read_text(encoding="utf-8"))["overlays"]
    cine = json.loads((PROJECT / "cine_scenes.json").read_text(encoding="utf-8"))["scenes"]
    for c in cine:
        # cine2/ — свежие перерендеры (cine_02 без 20/20, полированный глобус);
        # если там нет — берём оригинал из cine/ (напр. любимая cine_01).
        fresh = PROJECT / "assets" / "cine2" / f"{c['id']}.mov"
        c["file"] = str(fresh if fresh.exists() else PROJECT / "assets" / "cine" / f"{c['id']}.mov")
        c.setdefault("type", "cine")

    spans = [(c["start"], c["start"] + c["duration_sec"]) for c in cine]
    quick2 = [q for q in quick if not any(s <= q["start"] < e for s, e in spans)]
    removed = len(quick) - len(quick2)

    all_graphics = quick2 + cine
    all_graphics.sort(key=lambda g: g["start"])

    seq = pymiere.objects.app.project.activeSequence
    v = seq.videoTracks[OVERLAY_TRACK]
    for cl in reversed(list(v.clips)):
        cl.remove(False, False)

    n = place_overlays(seq, all_graphics, PROJECT.resolve(), track_idx=OVERLAY_TRACK)
    pymiere.objects.app.project.save()
    print(f"кино-сцен: {len(cine)} | быстрых поглощено сценами: {removed} | "
          f"уложено всего: {n}")


if __name__ == "__main__":
    main()
