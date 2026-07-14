"""LLM-режиссёр кино-сцен → projects/.../cine_scenes.json.
Запуск:
    PYTHONUTF8=1 ../webik-pipeline/.venv/Scripts/python.exe tests/direct_scenes.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.overlays.director import direct_scenes

PROJECT = Path("projects/2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-")


def main():
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    alignment = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))
    result = direct_scenes(scenes, alignment, max_scenes=2)

    out = PROJECT / "cine_scenes.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n→ {out} ({len(result['scenes'])} сцен)")
    for sc in result["scenes"]:
        blocks = [b for b in sc["props"]["blocks"] if b["kind"] == "stat"]
        print(f"  {sc['id']} @ {sc['start']}s · {sc['duration_sec']}s · "
              f"биты: {[(b['value'], b['label']) for b in blocks]}")


if __name__ == "__main__":
    main()
