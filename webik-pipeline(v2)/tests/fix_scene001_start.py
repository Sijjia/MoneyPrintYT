"""Фикс: на V3 в слоте 0:00 стоит чужой scene_320 вместо scene_001. Перекрываем
правильным триммед-клипом scene_001 (overwriteClip, тайминг слота сохраняем)."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pymiere
from pymiere.wrappers import time_from_seconds
from services.premiere_template.timeline_ops import import_media

PROJ = Path(__file__).resolve().parent.parent / "projects" / "2026-08-08_aysberg-severnoy-korei-samye-zakrytye-zhutkie-i-maloizvestny"
SCENE001 = PROJ / "assets" / "video_stock" / "_trimmed" / "scene_001.mp4"


def main():
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[2]
    # найти клип в слоте 0:00
    target = None
    for i in range(v3.clips.numItems):
        c = v3.clips[i]
        if c.start.seconds < 0.2:
            target = c; break
    if not target:
        print("клип в 0:00 не найден"); return 1
    slot_start = target.start.seconds; slot_end = target.end.seconds
    print(f"слот 0:00 сейчас: {target.name} [{slot_start:.2f}-{slot_end:.2f}]")
    if not (SCENE001.exists() and SCENE001.stat().st_size > 5000):
        print(f"нет файла {SCENE001}"); return 1
    item = import_media(SCENE001)
    if not item:
        print("import scene_001 не удался"); return 1
    # overwrite на V3 в позицию 0:00
    v3.overwriteClip(item, time_from_seconds(slot_start))
    time.sleep(1.0)
    # проверка
    v3b = seq.videoTracks[2]
    now = None
    for i in range(v3b.clips.numItems):
        c = v3b.clips[i]
        if c.start.seconds < 0.2: now = c.name; break
    print(f"слот 0:00 теперь: {now}")
    pymiere.objects.app.project.save()
    print("сохранено")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
