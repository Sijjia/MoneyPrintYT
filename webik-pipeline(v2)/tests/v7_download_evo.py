"""Качает V7-киновставки по v7_inserts.json, нормализует в DNxHR ровно на ~6с.
Файлы: assets/v7_inserts/v7_{scene}_{start}_6.mov (имя под v7_place_evo). БЕЗ Premiere."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tests.cutaway_source_place import fetch_robust, normalize

PROJECT = ROOT / "projects" / "2026-08-18_aysberg-evolyutsii-temnaya-i-zapretnaya-storona-evolyutsii-o"
OUT = (PROJECT / "assets" / "v7_inserts").resolve()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    ins = json.loads((PROJECT / "v7_inserts.json").read_text(encoding="utf-8"))["inserts"]
    print(f"вставок: {len(ins)}")
    ok = 0
    for i, c in enumerate(ins, 1):
        sid = c["scene_id"]; q = c.get("query", ""); dur = min(float(c["dur"]), 6.0); start = int(float(c["start"]))
        dst = OUT / f"v7_{sid}_{start}_6.mov"
        print(f"\n[{i}/{len(ins)}] {sid} @ {start//60}:{start%60:02d} ({dur:.1f}с) · '{q}'", flush=True)
        if dst.exists() and dst.stat().st_size > 5000:
            print("    кэш"); ok += 1; continue
        raw = fetch_robust(q, dur, f"v7_{sid}_{start}", fact=c.get("idea", ""), idea=c.get("idea", ""))
        if raw is None or not Path(raw).exists():
            print("    не скачалось"); continue
        if normalize(Path(raw), dst, dur):
            ok += 1; print(f"    ✓ {dst.name}")
    print(f"\nготово {ok}/{len(ins)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
