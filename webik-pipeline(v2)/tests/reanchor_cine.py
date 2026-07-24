"""Переякоривание кино-сцен (cine_scenes.json — без anchor/scene_id, только start)
под новый alignment через тайм-варп old→new по общим сценам."""
import json
import sys
from pathlib import Path
from bisect import bisect_right

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-"


def main() -> int:
    old = json.loads((PROJECT / "assets" / "alignment_raw_dedup.json").read_text(encoding="utf-8"))["scenes"]
    new = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    # пары (old_start, new_start) по общим сценам, сорт по old
    pairs = sorted(((old[s]["start"], new[s]["start"]) for s in old if s in new and old[s].get("n_words", 1)),
                   key=lambda p: p[0])
    oxs = [p[0] for p in pairs]
    nxs = [p[1] for p in pairs]

    def warp(t: float) -> float:
        if t <= oxs[0]:
            return round(t + (nxs[0] - oxs[0]), 2)
        if t >= oxs[-1]:
            return round(t + (nxs[-1] - oxs[-1]), 2)
        i = bisect_right(oxs, t) - 1
        o0, o1, n0, n1 = oxs[i], oxs[i + 1], nxs[i], nxs[i + 1]
        frac = (t - o0) / (o1 - o0) if o1 > o0 else 0
        return round(n0 + frac * (n1 - n0), 2)

    cs = json.loads((PROJECT / "cine_scenes.json").read_text(encoding="utf-8"))
    for c in cs["scenes"]:
        old_s = c["start"]
        c["start"] = warp(old_s)
        print(f"  {c['id']:10} {old_s:8.1f} -> {c['start']:8.1f}")
    cs["scenes"].sort(key=lambda c: c["start"])
    (PROJECT / "cine_scenes.json").write_text(json.dumps(cs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"cine: переякорено {len(cs['scenes'])} тайм-варпом")
    return 0


if __name__ == "__main__":
    sys.exit(main())
