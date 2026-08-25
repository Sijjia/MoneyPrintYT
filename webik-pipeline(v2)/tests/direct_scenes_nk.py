"""LLM-режиссёр кино-сцен → projects/.../cine_scenes.json.
Запуск:
    PYTHONUTF8=1 ../webik-pipeline/.venv/Scripts/python.exe tests/direct_scenes.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.overlays.director import direct_scenes

PROJECT = Path("projects/2026-08-08_aysberg-severnoy-korei-samye-zakrytye-zhutkie-i-maloizvestny")


def main():
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    alignment = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))
    result = direct_scenes(scenes, alignment, max_scenes=8)

    out = PROJECT / "cine_scenes.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n→ {out} ({len(result['scenes'])} сцен)")
    for sc in result["scenes"]:
        if sc["composition"] == "Globe3D":
            places = [p["label"] for p in sc["props"]["places"]]
            print(f"  {sc['id']} @ {sc['start']}s · глобус · {places}")
        else:
            kinds = [b["kind"] for b in sc["props"]["blocks"]]
            print(f"  {sc['id']} @ {sc['start']}s · {sc['duration_sec']}s · блоки: {kinds}")


if __name__ == "__main__":
    main()
