"""Проход по именам лидеров → рендер NameLabel → domерж в overlays_rendered.json.
Плашки лидеров сект (нижняя треть), сверенные с закадром. Запуск:
    PYTHONUTF8=1 ../webik-pipeline/.venv/Scripts/python.exe tests/detect_names.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.overlays.names import detect_names
from services.overlays.render_bridge import render_overlays
from services.overlays.themes import apply_theme, pick_theme

PROJECT = Path("projects/2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-")


def main():
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    alignment = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))
    names = detect_names(scenes, alignment)["overlays"]
    if not names:
        print("Имён не найдено")
        return

    ovr = PROJECT / ".overlay_theme"
    theme = pick_theme(PROJECT.name, override=ovr.read_text(encoding="utf-8").strip() if ovr.exists() else None)
    apply_theme(names, theme)
    rendered = render_overlays(names, PROJECT / "assets" / "overlays4")

    manifest = PROJECT / "overlays_rendered.json"
    existing = json.loads(manifest.read_text(encoding="utf-8"))["overlays"] if manifest.exists() else []
    have = {o["id"] for o in existing}
    merged = existing + [n for n in rendered if n["id"] not in have]
    merged.sort(key=lambda o: o["start"])
    manifest.write_text(json.dumps({"overlays": merged}, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n→ {len(rendered)} плашек имён, всего оверлеев {len(merged)}")
    for o in rendered:
        t = int(o["start"])
        print(f"  {t // 60}:{t % 60:02d}  {o['props']['name']} — {o['props']['sub']}")


if __name__ == "__main__":
    main()
