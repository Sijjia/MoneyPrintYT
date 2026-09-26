"""Переукладка слоёв DreamWorks с УНИКАЛЬНЫМИ именами (import_media матчит по имени —
scene_XXX.mp4 коллизил с телом). photozoom+фиксы → V3, графика → V7. Чистим V7, один save."""
import json, os, shutil, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
from pymiere.wrappers import time_from_seconds
from services.premiere_template.timeline_ops import import_media

PROJECT = ROOT / "projects" / "2026-08-25_aysberg-dreamworks-lost-media-i-temnaya-skrytaya-storona-stu"
PRPROJ = PROJECT / "project_template.prproj"
UNIQ = PROJECT / "assets" / "_uniq"
UNIQ.mkdir(parents=True, exist_ok=True)


def uniq_copy(src: Path, prefix: str, sid: str) -> Path:
    dst = UNIQ / f"{prefix}_{sid}.mp4"
    if not (dst.exists() and dst.stat().st_size == src.stat().st_size):
        shutil.copy(src, dst)
    return dst


def main() -> int:
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    man = json.loads((PROJECT / "assets" / "images" / "manifest.json").read_text(encoding="utf-8"))
    plan = json.loads((PROJECT / "graphics_plan_v2_dw.json").read_text(encoding="utf-8"))
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[2]
    v7 = seq.videoTracks[6]

    # чистим V7 (там сейчас ошибочно тело)
    for cl in reversed(list(v7.clips)):
        try: cl.remove(False, False)
        except Exception: pass
    print(f"[0] V7 очищен → {v7.clips.numItems}", flush=True)

    def place(track, src: Path, prefix: str, sid: str):
        u = uniq_copy(src, prefix, sid)
        it = import_media(u)
        if it is None: return False
        track.overwriteClip(it, time_from_seconds(round(al[sid]["start"], 2)))
        return True

    # 1) photozoom → V3
    n = 0
    for sid in al:
        f = PROJECT / "assets" / "photozoom" / f"{sid}.mp4"
        if f.exists() and man.get(sid, {}).get("kind") == "image":
            if place(v3, f, "pz", sid): n += 1
    print(f"[1] photozoom → V3: {n}", flush=True)

    # 2) фиксы → V3
    n = 0
    for f in sorted((PROJECT / "assets" / "video_stock" / "_fixed").glob("*.mp4")):
        sid = f.stem
        if sid in al and place(v3, f, "fx", sid): n += 1
    print(f"[2] фиксы → V3: {n}", flush=True)

    # 3) графика → V7
    n = 0
    for sid in sorted(plan.keys(), key=lambda s: al.get(s, {}).get("start", 0)):
        f = PROJECT / "assets" / "graphics" / f"{sid}.mp4"
        if sid in al and f.exists():
            if place(v7, f, "gfx", sid): n += 1
    print(f"[3] графика → V7: {n}", flush=True)

    before = PRPROJ.stat().st_mtime if PRPROJ.exists() else 0
    pymiere.objects.app.project.save(); time.sleep(2.0)
    after = PRPROJ.stat().st_mtime if PRPROJ.exists() else 0
    # контроль: путь первого клипа V7
    try: mp = v7.clips[0].projectItem.getMediaPath()
    except Exception: mp = "?"
    print(f"V3={v3.clips.numItems} V7={v7.clips.numItems}")
    print(f"V7[0] path=...{mp[-38:]}  ({'ГРАФИКА OK' if 'graphics' in mp or '_uniq' in mp else 'НЕ графика!'})")
    print(f"СЕЙВ: {'ОБНОВИЛСЯ ✓' if after > before else 'НЕ изменился ✗'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
