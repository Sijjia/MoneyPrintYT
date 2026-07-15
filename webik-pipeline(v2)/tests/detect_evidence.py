"""Проход по АРХИВ-отсылкам → рендер EvidenceFrame → domерж в overlays_rendered.json.
Рамки «АРХИВ»/«ФОТО»/«ЗАПИСЬ»/«ДОКУМЕНТ» там, где закадр ссылается на документальный
материал (с верификацией по слову-триггеру). Запуск:
    PYTHONUTF8=1 ../webik-pipeline/.venv/Scripts/python.exe tests/detect_evidence.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.overlays.evidence import detect_evidence
from services.overlays.render_bridge import render_overlays
from services.overlays.themes import apply_theme, pick_theme

PROJECT = Path("projects/2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-")


def main():
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    alignment = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))
    ev = detect_evidence(scenes, alignment)["overlays"]
    if not ev:
        print("АРХИВ-отсылок не найдено")
        return

    ovr = PROJECT / ".overlay_theme"
    theme = pick_theme(PROJECT.name, override=ovr.read_text(encoding="utf-8").strip() if ovr.exists() else None)
    apply_theme(ev, theme)
    rendered = render_overlays(ev, PROJECT / "assets" / "overlays4")

    manifest = PROJECT / "overlays_rendered.json"
    existing = json.loads(manifest.read_text(encoding="utf-8"))["overlays"] if manifest.exists() else []
    have = {o["id"] for o in existing}
    merged = existing + [e for e in rendered if e["id"] not in have]
    merged.sort(key=lambda o: o["start"])
    manifest.write_text(json.dumps({"overlays": merged}, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n→ {len(rendered)} АРХИВ-рамок, всего оверлеев {len(merged)}")
    for o in rendered:
        t = int(o["start"])
        print(f"  {t // 60}:{t % 60:02d}  [{o['props']['label']}] {o['props']['sub']}")


if __name__ == "__main__":
    main()
