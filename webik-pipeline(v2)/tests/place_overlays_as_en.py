"""Кладёт отрендеренные оверлеи Adult Swim (overlays_rendered.json) на V7 (idx6)
активной секвенции. Premiere с проектом открыт.
  PYTHONUTF8=1 ../webik-pipeline/.venv/Scripts/python.exe tests/place_overlays_as.py
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pymiere
from services.premiere.overlay_placer import place_overlays

PROJECT = Path("projects/2026-08-31_aysberg-adult-swim-temnaya-skrytaya-storona-nochnogo-bloka-c_EN")
OVERLAY_TRACK = 6  # V7 (V8 оставляем под вставки)


def main():
    data = json.loads((PROJECT / "overlays_rendered.json").read_text(encoding="utf-8"))
    overlays = data["overlays"]
    seq = pymiere.objects.app.project.activeSequence
    print(f"секвенция: {seq.name} | оверлеев к укладке: {len(overlays)}")

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
