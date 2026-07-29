"""Курирование вставок по фидбеку Айдара (работает на открытом проекте-базе, где
тело V3 оригинальное + gapfill врезаны в V3 + cutaway лежат overlay на V7):

1. V3: убрать gapfill, налезающие на ПЛАШКИ ТЕМ (V4) — под названием темы не должно
   быть видео (там вернётся оригинальный фон/чёрный, Айдар ОК). Mid-body gapfill
   (реальные чёрные дыры типа 6:59) — ОСТАВИТЬ.
2. V7: убрать cutaway на плашках тем + проредить до ~TARGET лучших (равномерно по ролику).

Ничего не врезает — только чистит слои (безопасно). Отдельный шаг врежет оставшиеся.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pymiere

TARGET = 12  # сколько cutaway оставить в теле


def name_of(clip):
    try:
        return Path(clip.projectItem.getMediaPath()).name.lower()
    except Exception:
        return clip.name.lower()


def main() -> int:
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[2]; v4 = seq.videoTracks[3]; v7 = seq.videoTracks[6]
    plaques = [(c.start.seconds, c.end.seconds) for c in v4.clips]

    def on_plaque(a, b):
        return any(a < pb and b > pa for pa, pb in plaques)

    # 1) V3: снять gapfill на плашках
    removed_gf = 0
    for cl in reversed(list(v3.clips)):
        n = name_of(cl)
        if n.startswith("gapfill") and on_plaque(cl.start.seconds, cl.end.seconds):
            cl.remove(False, False); removed_gf += 1
    print(f"V3: убрано gapfill с плашек тем: {removed_gf}")

    # 2) V7: снять cutaway на плашках
    cutaways = []
    for cl in list(v7.clips):
        if on_plaque(cl.start.seconds, cl.end.seconds):
            cl.remove(False, False)
        else:
            cutaways.append(cl)
    print(f"V7: cutaway вне плашек: {len(cutaways)}")

    # 3) проредить до TARGET равномерно по времени
    cutaways.sort(key=lambda c: c.start.seconds)
    if len(cutaways) > TARGET:
        keep_idx = {round(i * (len(cutaways) - 1) / (TARGET - 1)) for i in range(TARGET)}
        removed = 0
        for i, cl in enumerate(cutaways):
            if i not in keep_idx:
                cl.remove(False, False); removed += 1
        print(f"V7: проредил, убрал {removed}, осталось {len(cutaways) - removed}")
    else:
        print(f"V7: прореживание не нужно ({len(cutaways)} <= {TARGET})")

    pymiere.objects.app.project.save()
    kept = [c for c in v7.clips]
    print(f"\nИТОГ: V7 cutaway осталось {len(kept)}, проект сохранён")
    for c in sorted(kept, key=lambda x: x.start.seconds):
        a = c.start.seconds
        print(f"  {int(a)//60:02d}:{int(a)%60:02d}  {name_of(c)[:36]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
