"""Качает сцен-вставки (аниме/фильм/мультик) по v7_inserts.json, нормализует в
DNxHR ровно на длину сцены. БЕЗ Premiere. Расстановку делает v7_place.py.
Файлы: assets/v7_inserts/v7_{scene}_{start}.mov
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests.cutaway_source_place import fetch_robust, normalize, PROJECT

OUT = (PROJECT / "assets" / "v7_inserts").resolve()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    ins = json.loads((PROJECT / "v7_inserts.json").read_text(encoding="utf-8"))["inserts"]
    print(f"сцен-вставок: {len(ins)}")
    ok = 0
    for i, c in enumerate(ins, 1):
        sid = c["scene_id"]; q = c.get("query", ""); dur = float(c["dur"]); start = int(float(c["start"]))
        tag = f"v7_{sid}_{start}"
        dst = OUT / f"{tag}.mov"
        print(f"\n[{i}/{len(ins)}] {sid} @ {start//60}:{start%60:02d} ({dur:.1f}с) · {c.get('source')} · '{q}'", flush=True)
        if dst.exists() and dst.stat().st_size > 5000:
            print("    готов (кэш)"); ok += 1; continue
        raw = fetch_robust(q, dur, tag, fact=c.get("idea", ""), idea=c.get("idea", ""))
        if raw is None or not Path(raw).exists():
            print("    не скачалось — пропуск"); continue
        if normalize(Path(raw), dst, dur):
            ok += 1; print(f"    ✓ {dst.name}")
    print(f"\nготово {ok}/{len(ins)} .mov")
    return 0


if __name__ == "__main__":
    sys.exit(main())
