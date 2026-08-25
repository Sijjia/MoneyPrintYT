"""Рендер КИНО-СЦЕН (cine_scenes.json, composition=Scene, 3D-камера) → assets/cine/*.mov."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.overlays.render_bridge import render_overlays
from services.overlays.themes import pick_theme, apply_theme

PROJECT = Path("projects/2026-08-08_aysberg-severnoy-korei-samye-zakrytye-zhutkie-i-maloizvestny")


def main():
    scenes = json.loads((PROJECT / "cine_scenes.json").read_text(encoding="utf-8"))["scenes"]
    ovr = PROJECT / ".overlay_theme"
    theme = pick_theme(PROJECT.name, override=ovr.read_text(encoding="utf-8").strip() if ovr.exists() else None)
    apply_theme(scenes, theme)
    for s in scenes:
        s.setdefault("type", "cine")  # render_bridge логирует ov['type']
    print(f"тема: {theme['name']} ({theme['accent']}); кино-сцен: {len(scenes)}")
    out_dir = PROJECT / "assets" / "cine"
    render_overlays(scenes, out_dir, overwrite=False)
    print(f"→ {out_dir}")


if __name__ == "__main__":
    main()
