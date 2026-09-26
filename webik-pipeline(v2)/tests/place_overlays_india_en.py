"""Кладёт отрендеренные оверлеи (overlays_rendered.json) на активную секвенцию
в открытом Premiere. Тест на живом собранном таймлайне.
Запуск:
    PYTHONUTF8=1 ../webik-pipeline/.venv/Scripts/python.exe tests/place_overlays.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pymiere

from services.premiere.overlay_placer import place_overlays

PROJECT = Path("projects/2026-09-22_aysberg-indii-misticheskaya-i-zagadochnaya-storona-strany_EN")


def main():
    data = json.loads((PROJECT / "overlays_rendered.json").read_text(encoding="utf-8"))
    overlays = data["overlays"]
    seq = pymiere.objects.app.project.activeSequence
    print(f"секвенция: {seq.name} | оверлеев к укладке: {len(overlays)}")

    # V8 — канонная дорожка оверлеев. Чистим её от прошлого прогона, кладём заново.
    OVERLAY_TRACK = 7  # V8
    v = seq.videoTracks[OVERLAY_TRACK]
    old = list(v.clips)
    if old:
        for c in reversed(old):
            c.remove(False, False)
        print(f"V{OVERLAY_TRACK + 1}: очищено {len(old)} старых оверлеев")

    n = place_overlays(seq, overlays, PROJECT.resolve(), track_idx=OVERLAY_TRACK)
    pymiere.objects.app.project.save()
    print(f"уложено {n}, проект сохранён")


if __name__ == "__main__":
    main()
