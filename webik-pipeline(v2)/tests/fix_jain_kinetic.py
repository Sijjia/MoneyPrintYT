"""Замена зацензуренного кинетика (НЕНАСИЛИЯ блюрилось) на исправленный
(РЕЛИГИЯ МИЛОСЕРДИЯ) из свежей папки arche3c. Снять старый V8-клип @572, положить новый.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pymiere
from services.premiere.overlay_placer import place_overlays

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-"

FIXED = {
    "id": "arch_j1", "type": "kinetic", "composition": "KineticType",
    "scene_id": "scene_091", "start": 572.0, "duration_sec": 4.5,
    "anchor": "у религии милосердия есть тёмная сторона",
    "file": str(PROJECT / "assets" / "arche3c" / "arch_j1.mov"),
    "props": {"lines": ["РЕЛИГИЯ МИЛОСЕРДИЯ", "И ГОЛОД ДО КОНЦА"], "highlight": "голод", "accent": "#d92828"},
}


def main() -> int:
    if not Path(FIXED["file"]).exists():
        print("нет исправленного файла"); return 1
    manifest = PROJECT / "overlays_rendered.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    by_id = {o["id"]: o for o in data["overlays"]}
    by_id["arch_j1"] = FIXED
    data["overlays"] = sorted(by_id.values(), key=lambda o: o["start"])
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    seq = pymiere.objects.app.project.activeSequence
    v8 = seq.videoTracks[7]
    removed = 0
    for c in reversed(list(v8.clips)):
        if 571.0 <= c.start.seconds <= 573.0:
            c.remove(False, False); removed += 1
    print(f"снят старый кинетик: {removed}")

    n = place_overlays(seq, [FIXED], PROJECT.resolve(), track_idx=7)
    pymiere.objects.app.project.save()
    print(f"уложено {n}, сохранено")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
