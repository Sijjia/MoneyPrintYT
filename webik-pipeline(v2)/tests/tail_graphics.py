"""Добавляет графику в хвост (альбиносы) — рендерит новые оверлеи и кладёт на V8
БЕЗ очистки существующих (append). Свободные слоты, без конфликтов.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pymiere
from services.overlays.render_bridge import render_overlays
from services.overlays.themes import pick_theme, apply_theme
from services.premiere.overlay_placer import place_overlays

PROJECT = Path("projects/2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-")
V8 = 7

NEW = [
    {"id": "tail_g1", "type": "shock", "composition": "ShockCounter", "scene_id": "scene_178",
     "anchor": "охотятся как на животных", "start": 1326.0, "duration_sec": 5.0,
     "props": {"from": 0, "to": 76, "label": "убитых альбиносов", "sub": "Восточная Африка · документировано", "accent": "#d92828"}},
    {"id": "tail_g2", "type": "crowd", "composition": "CrowdPictograph", "scene_id": "scene_181",
     "anchor": "прятать в специальных охраняемых", "start": 1362.0, "duration_sec": 5.0,
     "props": {"total": 76, "filled": 76, "label": "жертв", "sub": "охота на альбиносов · Танзания", "accent": "#d92828"}},
]


def main():
    theme = pick_theme(PROJECT.name)
    apply_theme(NEW, theme)
    out_dir = PROJECT / "assets" / "overlays_tail"
    rendered = render_overlays(NEW, out_dir)
    print(f"отрендерено: {len(rendered)}/{len(NEW)}")
    for r in rendered:
        print("  ", r["id"], r.get("file", "")[-40:])

    seq = pymiere.objects.app.project.activeSequence
    n = place_overlays(seq, rendered, PROJECT.resolve(), track_idx=V8)  # append, НЕ чистим V8
    pymiere.objects.app.project.save()
    print(f"добавлено на V8: {n}, проект сохранён")


if __name__ == "__main__":
    main()
