"""Графика на тему «Грабовой» (5:00–6:23): таймлайн судебной хроники.

TimelineJourney @359.5 — приговор и после (2008 · 11 лет → 8 лет → 2010 УДО →
за рубежом), синхрон с закадром. Ставится АДДИТИВНО на V8 (правки Айдара не трогаем),
перекрывает старый ov_005 (Timeline-стат, теперь избыточен) и убирает его из манифеста.

Рендер в assets/arche3/, домерж в overlays_rendered.json, аддитивная укладка.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pymiere
from services.overlays.render_bridge import render_overlays
from services.premiere.overlay_placer import place_overlays

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-"
ACCENT = "#d92828"
OVERLAY_TRACK = 7

TL = {
    "id": "arch_g1",
    "type": "timeline",
    "composition": "TimelineJourney",
    "scene_id": "scene_045",
    "start": 359.5,
    "duration_sec": 13.0,
    "anchor": "Таганский суд Москвы приговорил его к 11 годам",
    "props": {
        "title": "Дело Грабового",
        "accent": ACCENT,
        "durationInFrames": 390,
        "events": [
            {"year": 2008, "label": "Приговор · 11 лет"},
            {"year": "8 лет", "label": "Мосгорсуд снизил"},
            {"year": 2010, "label": "Вышел по УДО"},
            {"year": "Сейчас", "label": "Семинары за рубежом"},
        ],
    },
}

DROP_IDS = {"ov_005"}  # старый Timeline-стат, перекрыт новым таймлайном


def main() -> int:
    rendered = render_overlays([TL], PROJECT / "assets" / "arche3", overwrite=True)
    if not rendered:
        print("рендер таймлайна упал")
        return 1

    manifest = PROJECT / "overlays_rendered.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    by_id = {o["id"]: o for o in data["overlays"] if o["id"] not in DROP_IDS}
    for r in rendered:
        by_id[r["id"]] = r
    data["overlays"] = sorted(by_id.values(), key=lambda o: o["start"])
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"манифест: убрано {DROP_IDS}, добавлено {[r['id'] for r in rendered]}, всего {len(data['overlays'])}")

    # аддитивная укладка нового таймлайна (overwriteClip уберёт ov_005 в этом окне)
    seq = pymiere.objects.app.project.activeSequence
    n = place_overlays(seq, rendered, PROJECT.resolve(), track_idx=OVERLAY_TRACK)
    pymiere.objects.app.project.save()
    print(f"уложено {n}, проект сохранён")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
