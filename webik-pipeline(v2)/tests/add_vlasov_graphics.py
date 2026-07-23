"""Добавляет графику на тему «Царская Империя» (Власов), 3:43–4:56.

Две полноэкранные сцены, привязанные к словам закадра:
  arch_v1  KineticType  @238.5  — самопровозглашённые титулы «ЦАРЬ · ПАТРИАРХ · ИСКУПИТЕЛЬ»
  arch_v2  NetworkGraph @250.0  — структура тотального контроля: всё стекается к лидеру

Рендер в assets/arche3/, домерж в overlays_rendered.json (дедуп по id).
Уложить потом: tests/place_all_graphics.py → tests/place_intro.py.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.overlays.render_bridge import render_overlays

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-"
ACCENT = "#d92828"

# nodeStart в кадрах от начала клипа (старт 250.0с), синхрон с закадром:
#  «все деньги» 255.86 → 176 · «связи с родственниками» 256.72 → 202
#  «где приказывал» 258.44 → 253 · «делали что велел» 260.40 → 312
NET = {
    "id": "arch_v2",
    "type": "network",
    "composition": "NetworkGraph",
    "scene_id": "scene_030",
    "start": 250.0,
    "duration_sec": 12.4,
    "anchor": "Власов построил классическую тоталитарную секту",
    "props": {
        "title": "Жёсткий контроль",
        "titleStart": 60,
        "durationInFrames": 372,
        "accent": ACCENT,
        "nodes": [
            {"label": "Власов", "x": 50, "y": 49, "hot": True},
            {"label": "Все деньги", "x": 71, "y": 26},
            {"label": "Разрыв с роднёй", "x": 71, "y": 72},
            {"label": "Жизнь по приказу", "x": 29, "y": 72},
            {"label": "Полное подчинение", "x": 29, "y": 26},
        ],
        "edges": [[0, 1], [0, 2], [0, 3], [0, 4]],
        "nodeStart": [4, 176, 202, 253, 312],
    },
}

KIN = {
    "id": "arch_v1",
    "type": "kinetic",
    "composition": "KineticType",
    "scene_id": "scene_028",
    "start": 238.5,
    "duration_sec": 4.03,
    "anchor": "объявил себя царём-патриархом-искупителем",
    "props": {
        "lines": ["ЦАРЬ ПАТРИАРХ ИСКУПИТЕЛЬ"],
        "highlight": "искупитель",
        "accent": ACCENT,
    },
}

NEW = [KIN, NET]


def main() -> int:
    out_dir = PROJECT / "assets" / "arche3"
    rendered = render_overlays(NEW, out_dir, overwrite=True)
    if len(rendered) != len(NEW):
        print(f"ВНИМАНИЕ: отрендерено {len(rendered)}/{len(NEW)}")

    manifest = PROJECT / "overlays_rendered.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    by_id = {o["id"]: o for o in data["overlays"]}
    for r in rendered:
        by_id[r["id"]] = r
    data["overlays"] = sorted(by_id.values(), key=lambda o: o["start"])
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"домержено {len(rendered)}, всего оверлеев: {len(data['overlays'])}")
    for r in rendered:
        print(f"  {r['id']} [{r['type']}] @{r['start']} → {Path(r['file']).name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
