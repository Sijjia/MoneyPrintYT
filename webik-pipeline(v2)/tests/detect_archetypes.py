"""Детектор мощных полноэкранных приёмов (толпа/шок/заливка/таймлайн) → сухой прогон.
Печатает найденное со сверкой чисел; НЕ рендерит и НЕ кладёт (кураторский шаг —
что реально ставить, решаем отдельно). Запуск:
    PYTHONUTF8=1 ../webik-pipeline/.venv/Scripts/python.exe tests/detect_archetypes.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.overlays.archetypes import detect_archetypes

PROJECT = Path("projects/2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-")


def main():
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    alignment = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))
    res = detect_archetypes(scenes, alignment)
    (PROJECT / "archetypes.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n→ {len(res['overlays'])} приёмов (сверены с закадром)")
    for o in res["overlays"]:
        t = int(o["start"])
        p = o["props"]
        if o["type"] == "crowd":
            d = f"{p['filled']} из {p['total']} · {p['label']}"
        elif o["type"] == "shock":
            d = f"{p['from']}→{p['to']} · {p['label']}"
        elif o["type"] == "fill":
            d = f"{p['percent']}% · {p['label']}"
        else:
            d = f"{p['title']}: " + ", ".join(f"{e['year']} {e['label']}" for e in p["events"])
        print(f"  {t // 60}:{t % 60:02d}  [{o['type']:8}] {d}")


if __name__ == "__main__":
    main()
