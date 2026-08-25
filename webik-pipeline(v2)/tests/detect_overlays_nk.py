"""Прогон LLM-детектора динамических оверлеев → projects/.../overlays.json.
Запуск:
    PYTHONUTF8=1 ../webik-pipeline/.venv/Scripts/python.exe tests/detect_overlays.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.overlays.detector import detect_overlays

PROJECT = Path("projects/2026-08-08_aysberg-severnoy-korei-samye-zakrytye-zhutkie-i-maloizvestny")


def main():
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    alignment = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))
    result = detect_overlays(
        scenes,
        alignment,
        max_per_level=13,
        min_gap_sec=5.0,
        type_caps={"name": 3, "phrase": 3, "stat": 9, "compare": 4},
    )

    out = PROJECT / "overlays.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n→ {out} ({len(result['overlays'])} оверлеев)")
    for ov in result["overlays"]:
        p = ov["props"]
        desc = p.get("value") or p.get("name") or p.get("phrase")
        print(f"  {ov['start']:7.1f}s  [{ov['type']:6}] {ov['scene_id']:11} {desc!r}")


if __name__ == "__main__":
    main()
