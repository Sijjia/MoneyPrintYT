"""Денежная графика на «сотни тысяч рублей за сеанс» (сцена 036, @314.9).

KineticType, аддитивно на V8. Заполняет графический провал 307–335.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pymiere
from services.overlays.render_bridge import render_overlays
from services.premiere.overlay_placer import place_overlays

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-"

KIN = {
    "id": "arch_g2",
    "type": "kinetic",
    "composition": "KineticType",
    "scene_id": "scene_036",
    "start": 314.9,
    "duration_sec": 4.73,
    "anchor": "десятки, а иногда и сотни тысяч рублей за сеанс воскрешения",
    "props": {
        "lines": ["СОТНИ ТЫСЯЧ РУБЛЕЙ", "ЗА «СЕАНС ВОСКРЕШЕНИЯ»"],
        "highlight": "тысяч",
        "accent": "#d92828",
    },
}


def main() -> int:
    rendered = render_overlays([KIN], PROJECT / "assets" / "arche3", overwrite=True)
    if not rendered:
        print("рендер упал"); return 1
    manifest = PROJECT / "overlays_rendered.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    by_id = {o["id"]: o for o in data["overlays"]}
    for r in rendered:
        by_id[r["id"]] = r
    data["overlays"] = sorted(by_id.values(), key=lambda o: o["start"])
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    seq = pymiere.objects.app.project.activeSequence
    n = place_overlays(seq, rendered, PROJECT.resolve(), track_idx=7)
    pymiere.objects.app.project.save()
    print(f"уложено {n}, всего оверлеев {len(data['overlays'])}, сохранено")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
