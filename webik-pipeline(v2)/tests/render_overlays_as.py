"""Рендер оверлеев Adult Swim из overlays.json → assets/overlays/*.mov (прозрачные).
  PYTHONUTF8=1 ../webik-pipeline/.venv/Scripts/python.exe tests/render_overlays_as.py
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.overlays.render_bridge import render_overlays
from services.overlays.themes import pick_theme, apply_theme

PROJECT = Path("projects/2026-08-31_aysberg-adult-swim-temnaya-skrytaya-storona-nochnogo-bloka-c")


def main():
    data = json.loads((PROJECT / "overlays.json").read_text(encoding="utf-8"))
    overlays = data["overlays"]
    ovr_file = PROJECT / ".overlay_theme"
    override = ovr_file.read_text(encoding="utf-8").strip() if ovr_file.exists() else None
    theme = pick_theme(PROJECT.name, override=override)
    apply_theme(overlays, theme)
    print(f"тема проекта: {theme['name']} ({theme['accent']}), align={theme['align']}")

    out_dir = PROJECT / "assets" / "overlays"
    rendered = render_overlays(overlays, out_dir)
    manifest = PROJECT / "overlays_rendered.json"
    manifest.write_text(json.dumps({"overlays": rendered}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n→ {manifest} ({len(rendered)}/{len(overlays)} готово)")


if __name__ == "__main__":
    main()
