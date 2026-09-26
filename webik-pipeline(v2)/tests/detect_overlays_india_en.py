"""Прогон LLM-детектора динамических оверлеев → projects/.../overlays.json.
Запуск:
    PYTHONUTF8=1 ../webik-pipeline/.venv/Scripts/python.exe tests/detect_overlays.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.overlays.detector import detect_overlays

PROJECT = Path("projects/2026-09-22_aysberg-indii-misticheskaya-i-zagadochnaya-storona-strany_EN")

SYSTEM_EN = (
    "You are the motion-graphics art director for an ENGLISH-language dark 'iceberg' documentary "
    "YouTube channel about the mystical and hidden side of India. Pick ONLY the most striking moments "
    "in the narration and reinforce them with an animated overlay. Be sparse: most scenes get NOTHING. "
    "Overloading looks cheap. For each moment pick the MOST FITTING type. "
    "CRITICAL: ALL overlay text — every label, name, phrase, title, unit and caption — MUST be written "
    "in ENGLISH. The 'anchor' must be the verbatim English words spoken in that scene. Never output Russian."
)


def main():
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    alignment = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))
    result = detect_overlays(
        scenes,
        alignment,
        max_per_level=11,
        min_gap_sec=6.0,
        type_caps={"name": 3, "phrase": 2, "stat": 7, "timeline": 1, "compare": 1, "percent": 2, "ratio": 2},
        system=SYSTEM_EN,
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
