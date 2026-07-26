"""Восстанавливает удалённые звуки машинки (typing_scene_XXX_<tag>.wav) с ТЕМ ЖЕ
именем/тегом, что у offline-клипов на A4, → клипы снова online. Потом re-link.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests.assemble_iceberg_test import TYPING_SFX_SRC, TW_CPS, TYPING_SFX_TAIL, trim_sfx

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-"
SFX_DIR = PROJECT / "assets" / "sfx"


def main() -> int:
    print("SRC:", TYPING_SFX_SRC, "exists:", TYPING_SFX_SRC.exists())
    if not TYPING_SFX_SRC.exists():
        print("НЕТ исходного звука машинки — не могу восстановить"); return 1

    # tag берём из имён offline-клипов A4
    import pymiere
    seq = pymiere.objects.app.project.activeSequence
    a4 = seq.audioTracks[3]
    jobs = []  # (sid, tag, clip)
    for i in range(a4.clips.numItems):
        c = a4.clips[i]
        m = re.match(r"typing_(scene_\d+)_(\d+)", c.name)
        if m:
            jobs.append((m.group(1), m.group(2), c))
    print(f"offline typing-клипов на A4: {len(jobs)}")

    # титулы тем из scenes.json (для длины трима)
    sc = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))
    items = sc if isinstance(sc, list) else sc["scenes"]
    title_by = {(s.get("id") or s.get("scene_id")): (s.get("voiceover") or "") for s in items}

    SFX_DIR.mkdir(parents=True, exist_ok=True)
    relinked = 0
    for sid, tag, clip in jobs:
        title = title_by.get(sid, "").strip().rstrip(".")
        dur = len(title.upper()) / max(1.0, TW_CPS) + TYPING_SFX_TAIL
        dst = SFX_DIR / f"typing_{sid}_{tag}.wav"
        if not dst.exists():
            trim_sfx(TYPING_SFX_SRC, dst, dur)
        # re-link клип на восстановленный файл
        try:
            clip.projectItem.changeMediaPath(str(dst.resolve()), True)
            relinked += 1
        except Exception as e:
            print(f"  {sid}: relink упал {e}")
    pymiere.objects.app.project.save()
    print(f"восстановлено+перелинковано {relinked}/{len(jobs)}, сохранено")
    return 0


if __name__ == "__main__":
    sys.exit(main())
