"""Рендер оверлеев из overlays.json → assets/overlays/*.mov (прозрачные).
Пишет overlays_rendered.json (с путями файлов) для Premiere-placer'а.
Запуск:
    PYTHONUTF8=1 ../webik-pipeline/.venv/Scripts/python.exe tests/render_overlays.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.overlays.render_bridge import render_overlays
from services.overlays.themes import pick_theme, apply_theme

PROJECT = Path("projects/2026-09-22_aysberg-indii-misticheskaya-i-zagadochnaya-storona-strany_EN")


def main():
    data = json.loads((PROJECT / "overlays.json").read_text(encoding="utf-8"))
    overlays = data["overlays"]

    # пер-видео тема (авто по имени проекта; файл .overlay_theme перебивает вручную)
    ovr_file = PROJECT / ".overlay_theme"
    override = ovr_file.read_text(encoding="utf-8").strip() if ovr_file.exists() else None
    theme = pick_theme(PROJECT.name, override=override)
    apply_theme(overlays, theme)
    print(f"тема проекта: {theme['name']} ({theme['accent']}), align={theme['align']}")

    out_dir = PROJECT / "assets" / "overlays"
    rendered = render_overlays(overlays, out_dir)

    manifest = PROJECT / "overlays_rendered.json"
    manifest.write_text(
        json.dumps({"overlays": rendered}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n→ {manifest} ({len(rendered)}/{len(overlays)} готово)")


if __name__ == "__main__":
    main()
