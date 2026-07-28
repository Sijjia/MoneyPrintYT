"""Ставит cutaway-вставки НЕ поверх (V7), а ВРЕЗАЕТ в основную видеодорожку V3
жёстким стыком: тело → вставка → тело. Закадр A1 играет поверх. Так вставка =
цельная сцена по смыслу, без просвечивания тела/графики (что давало «мелькание
на миллисекунду»).

- чистит старые cutaway с V7;
- overwrite на V3 в ПОРЯДКЕ ВРЕМЕНИ → пересекающиеся (2 образа на сцену) авто-
  подрезаются встык, без наложения;
- БЕЗ opacity-фейдов (жёсткий стык, ничего не просвечивает).

Файлы: assets/cutaways/cutaway_{sid}_{int(start)}.mov
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pymiere
from pymiere.wrappers import time_from_seconds
from services.premiere_template.timeline_ops import import_media

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-"
OUT = (PROJECT / "assets" / "cutaways").resolve()
BODY_TRACK = 2   # V3 — основная видеодорожка
CUT_TRACK = 6    # V7 — старый overlay (чистим)
MIN_DUR = 2.5    # если после подрезки встык осталось < этого — вставку пропускаем (не мелькание)


def main() -> int:
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[BODY_TRACK]
    v7 = seq.videoTracks[CUT_TRACK]

    # 1) снять старые вставки с V7 (overlay-подход)
    removed = 0
    for cl in reversed(list(v7.clips)):
        cl.remove(False, False); removed += 1
    print(f"снято с V7 (overlay): {removed}")

    # 2) собрать вставки, у которых есть .mov
    cuts = json.loads((PROJECT / "cutaways.json").read_text(encoding="utf-8"))["cutaways"]
    items = []
    for c in cuts:
        at = float(c["abs_start"])
        tag = f"cutaway_{c['scene_id']}_{int(at)}"
        mov = OUT / f"{tag}.mov"
        if mov.exists() and mov.stat().st_size > 5000:
            items.append((at, float(c.get("duration_sec", 8.0)), mov, c))
    items.sort(key=lambda x: x[0])
    print(f"вставок с готовым .mov: {len(items)}")

    # 3) отсев слишком коротких «щелей» после встык-подрезки: если следующая
    #    начинается меньше чем через MIN_DUR после текущей — текущая станет огрызком,
    #    лучше сдвинуть следующую вплотную к концу текущей (сохранив её длину).
    #    overwrite сам подрежет предыдущую; здесь только убираем совсем мелкие.
    cleaned = []
    for at, dur, mov, c in items:
        if cleaned:
            pat, pdur, *_ = cleaned[-1]
            if at - pat < MIN_DUR:      # предыдущая станет < MIN_DUR — двигаем текущую к её концу
                at = pat + pdur
        cleaned.append((at, dur, mov, c))

    # 4) overwrite на V3 в порядке времени (пересечения авто-подрезаются встык)
    placed = 0
    for at, dur, mov, c in cleaned:
        item = import_media(mov)
        if item is None:
            print(f"    import упал: {mov.name}"); continue
        try:
            v3.overwriteClip(item, time_from_seconds(round(at, 2)))
            placed += 1
            print(f"    ✓ {c['scene_id']} @ {at:.1f}s ({dur:.0f}с)")
        except Exception as e:
            print(f"    overwrite упал {c['scene_id']}: {str(e)[:100]}")

    pymiere.objects.app.project.save()
    print(f"\nВРЕЗАНО в V3: {placed}/{len(cleaned)} (жёсткий стык, без фейдов), проект сохранён")
    return 0


if __name__ == "__main__":
    sys.exit(main())
