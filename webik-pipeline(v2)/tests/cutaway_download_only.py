"""Скачивает+нормализует все cutaway-клипы в DNxHR .mov БЕЗ Premiere (тяжёлая часть).
Расстановку потом делает cutaway_source_place.py (найдёт готовые .mov в кэше и
только импортнёт+поставит+фейд). Так качаем независимо от состояния Premiere.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests.cutaway_source_place import fetch_robust, normalize, OUT, PROJECT


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    cuts = json.loads((PROJECT / "cutaways.json").read_text(encoding="utf-8"))["cutaways"]
    print(f"скачиваю {len(cuts)} клипов (без Premiere)")
    ok = 0
    for i, c in enumerate(cuts, 1):
        sid = c["scene_id"]; q = c.get("yt_query", ""); dur = float(c.get("duration_sec", 7.0))
        dst = OUT / f"cutaway_{sid}.mov"
        print(f"\n[{i}/{len(cuts)}] {sid} · {dur}с · '{q}'", flush=True)
        if dst.exists() and dst.stat().st_size > 5000:
            print("    готов (кэш)"); ok += 1; continue
        raw = fetch_robust(q, dur, f"cutaway_{sid}",
                           fact=c.get("narration_snippet", ""),
                           idea=f"{c.get('visual_element','')} — {c.get('idea','')}".strip(" —"))
        if raw is None or not Path(raw).exists():
            print("    не скачалось"); continue
        if normalize(Path(raw), dst, dur):
            ok += 1; print(f"    ✓ {dst.name}")
    print(f"\nготово {ok}/{len(cuts)} .mov в {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
