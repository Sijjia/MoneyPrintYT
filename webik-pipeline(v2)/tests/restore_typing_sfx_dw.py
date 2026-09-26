"""Восстанавливает удалённые звуки машинки DreamWorks: генерит файлы РОВНО по путям, на которые
ссылаются offline-клипы A4 (из getMediaPath), длина = длительность клипа + запас, затем форс-реконнект."""
import os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests.assemble_iceberg_test import TYPING_SFX_SRC, TYPING_SFX_TAIL, trim_sfx

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-08-25_aysberg-dreamworks-lost-media-i-temnaya-skrytaya-storona-stu"
TPS = 254016000000


def clip_dur(c):
    try: return c.duration.seconds
    except Exception:
        try: return c.duration.ticks / TPS
        except Exception: return 2.5


def main() -> int:
    if not TYPING_SFX_SRC.exists():
        print("НЕТ исходного звука машинки"); return 1
    import pymiere
    seq = pymiere.objects.app.project.activeSequence
    a4 = seq.audioTracks[3]
    # 1) генерим файлы по фактическим путям offline-клипов
    jobs = []
    for c in a4.clips:
        try: mp = c.projectItem.getMediaPath()
        except Exception: mp = ""
        if "typing" not in mp.lower(): continue
        jobs.append((c, mp))
    print(f"typing-клипов на A4: {len(jobs)}")
    made = 0
    for c, mp in jobs:
        dst = Path(mp)
        if not (dst.exists() and dst.stat().st_size > 1000):
            dst.parent.mkdir(parents=True, exist_ok=True)
            trim_sfx(TYPING_SFX_SRC, dst, clip_dur(c) + TYPING_SFX_TAIL + 0.3)
            made += 1
    print(f"сгенерено файлов: {made}/{len(jobs)}")
    # 2) форс-реконнект тем же путём
    relinked = 0
    for c, mp in jobs:
        try:
            c.projectItem.changeMediaPath(str(Path(mp).resolve()), True); relinked += 1
        except Exception as e:
            print(f"  relink fail {os.path.basename(mp)}: {str(e)[:50]}")
    before = (PROJECT / "project_template.prproj").stat().st_mtime
    pymiere.objects.app.project.save()
    import time; time.sleep(1.5)
    ok = "OK" if (PROJECT / "project_template.prproj").stat().st_mtime > before else "NO(модал?)"
    print(f"реконнект {relinked}/{len(jobs)} | save {ok}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
