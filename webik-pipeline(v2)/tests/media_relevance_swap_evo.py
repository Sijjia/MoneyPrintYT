"""ФАЗА 2 (Premiere): применяет swap_plan.json — подменяет клипы на V3 на
пересобранное релевантное медиа (монтажи/зумы). Матч по времени сцены (alignment)."""
import json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere

PROJECT = ROOT / "projects" / "2026-08-18_aysberg-evolyutsii-temnaya-i-zapretnaya-storona-evolyutsii-o"
PLAN = PROJECT / "swap_plan.json"
tps = 254016000000


def cstart(c): return c.start.seconds if hasattr(c.start, "seconds") else float(c.start.ticks) / tps


def main() -> int:
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[2]
    # индекс клипов V3 по старту
    clips = []
    for i in range(v3.clips.numItems):
        clips.append((cstart(v3.clips[i]), i))
    clips.sort()

    def clip_at(t):
        best = None; bd = 1e9
        for s, i in clips:
            d = abs(s - t)
            if d < bd: bd = d; best = i
        return best if bd < 1.2 else None

    done = miss = 0
    for sid, path in sorted(plan.items()):
        if sid not in al or not Path(path).exists():
            miss += 1; continue
        idx = clip_at(al[sid]["start"])
        if idx is None:
            miss += 1; print(f"  ✗ {sid}: слот не найден"); continue
        try:
            v3.clips[idx].projectItem.changeMediaPath(str(Path(path).resolve()), True)
            done += 1
            if done % 25 == 0: print(f"  ...{done} свапнуто")
        except Exception as e:
            miss += 1; print(f"  ✗ {sid}: {str(e)[:60]}")
    pymiere.objects.app.project.save()
    print(f"\nмедиа-свап: {done}/{len(plan)} (miss {miss}); проект сохранён")
    return 0


if __name__ == "__main__":
    sys.exit(main())
