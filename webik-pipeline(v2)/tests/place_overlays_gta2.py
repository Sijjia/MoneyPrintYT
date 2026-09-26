"""EN-укладка оверлеев ПЕР-КЛИПОВО (обход зависшего bulk importFiles): каждый .mov
импортируем по одному (import_media) и кладём на V7. Premiere открыт с EN.
  ../webik-pipeline/.venv/Scripts/python.exe tests/place_overlays_as_en2.py
"""
import json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
from pymiere.wrappers import time_from_seconds
from services.premiere_template.timeline_ops import import_media, _throttle

PROJECT = ROOT / "projects" / "2026-09-06_aysberg-gta-temnaya-storona-realnye-dela-vnutriigrovye-tayny"
OVERLAY_TRACK = 6  # V7


def main() -> int:
    data = json.loads((PROJECT / "overlays_rendered.json").read_text(encoding="utf-8"))
    overlays = data["overlays"]
    seq = pymiere.objects.app.project.activeSequence
    v = seq.videoTracks[OVERLAY_TRACK]
    # чистим V7 (в т.ч. диаг-клип)
    old = list(v.clips)
    for c in reversed(old):
        c.remove(False, False)
    print(f"V7 очищено: {len(old)} | к укладке: {len(overlays)}", flush=True)

    placed = 0
    for ov in overlays:
        raw = Path(ov.get("file", ""))
        cands = [raw] if raw.is_absolute() else [Path.cwd() / raw, PROJECT / raw,
                                                 PROJECT / "assets" / "overlays" / f"{ov['id']}.mov"]
        f = next((c.resolve() for c in cands if c.exists()), None)
        if f is None:
            print(f"  ✗ {ov['id']}: .mov не найден"); continue
        item = import_media(f)
        if item is None:
            print(f"  ✗ {ov['id']}: import None"); continue
        try:
            _throttle()
            v.overwriteClip(item, time_from_seconds(float(ov["start"])))
            placed += 1
            if placed % 10 == 0:
                print(f"  ...{placed}/{len(overlays)}", flush=True)
        except Exception as e:
            print(f"  ✗ {ov['id']}: place {str(e)[:50]}")

    pymiere.objects.app.project.save(); time.sleep(1.0)
    print(f"уложено {placed}/{len(overlays)}, сохранено", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
