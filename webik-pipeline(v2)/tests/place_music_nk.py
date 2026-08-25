"""Кладёт готовый bg_bed_levels.mp3 (прогрессия по уровням + даккинг) на A2 (idx1) с 0:00."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pymiere
from pymiere.wrappers import time_from_seconds
from services.premiere_template.timeline_ops import import_media

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-08-08_aysberg-severnoy-korei-samye-zakrytye-zhutkie-i-maloizvestny"
BED = (PROJECT / "assets" / "music" / "bg_bed_levels.mp3").resolve()
MUSIC_TRACK = 1  # A2


def main() -> int:
    if not BED.exists():
        print("нет bg_bed_levels.mp3 — сначала build_level_music_nk.sh"); return 1
    seq = pymiere.objects.app.project.activeSequence
    a2 = seq.audioTracks[MUSIC_TRACK]
    for cl in reversed(list(a2.clips)):
        cl.remove(False, False)
    item = import_media(BED)
    if item is None:
        print("import не удался"); return 1
    a2.overwriteClip(item, time_from_seconds(0.0))
    pymiere.objects.app.project.save()
    print(f"музыка на A2 с 0:00: {BED.name}; проект сохранён")
    return 0


if __name__ == "__main__":
    sys.exit(main())
