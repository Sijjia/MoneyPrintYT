"""Больше графики: Нигерия (дети в цепях) + Саллекхана (джайнская смерть от голода),
6:28–10:43. Разные типы, привязка по таймлайну (alignment сдвинут ~19.7с).

- arch_n1 CrowdPictograph 300 «в цепях» @472.5 — ЗАМЕНЯЕТ слабый ov_007 (CountUpBar 300)
- arch_n2 NetworkGraph «система школ» @524 (Кадуна·Катсина·Ибадан по всей стране)
- arch_j1 KineticType парадокс @572 «религия ненасилия — и голод до конца»
- arch_j2 TimelineJourney @610 закон о саллекхане (2015 запрет → ВС отменил → спор)

Аддитивно на V8 (правки Айдара не трогаем), ov_007 снимаем.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pymiere
from services.overlays.render_bridge import render_overlays
from services.premiere.overlay_placer import place_overlays

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-"
ACC = "#d92828"

CROWD = {
    "id": "arch_n1", "type": "crowd", "composition": "CrowdPictograph",
    "scene_id": "scene_083", "start": 472.5, "duration_sec": 5.3,
    "anchor": "освободила более трёхсот мальчиков в цепях",
    "props": {"total": 300, "filled": 300, "label": "в цепях", "sub": "Кадуна · 2019 · освобождены", "accent": ACC},
}
NET = {
    "id": "arch_n2", "type": "network", "composition": "NetworkGraph",
    "scene_id": "scene_087", "start": 524.0, "duration_sec": 9.5,
    "anchor": "похожие рейды в Катсине и Ибадане, проблема массовая",
    "props": {
        "title": "«Школы» по всей Нигерии · 2019",
        "titleStart": 8, "durationInFrames": 285, "accent": ACC,
        "nodes": [
            {"label": "«Школы»", "x": 50, "y": 49, "hot": True},
            {"label": "Кадуна", "x": 72, "y": 27},
            {"label": "Катсина", "x": 72, "y": 71},
            {"label": "Ибадан", "x": 28, "y": 71},
            {"label": "Одобрение властей", "x": 28, "y": 27},
        ],
        "edges": [[0, 1], [0, 2], [0, 3], [0, 4]],
        "nodeStart": [4, 40, 78, 108, 150],
    },
}
KIN = {
    "id": "arch_j1", "type": "kinetic", "composition": "KineticType",
    "scene_id": "scene_091", "start": 572.0, "duration_sec": 4.5,
    "anchor": "у религии милосердия есть тёмная сторона — ритуал саллекхана",
    "props": {"lines": ["РЕЛИГИЯ НЕНАСИЛИЯ", "И ГОЛОД ДО КОНЦА"], "highlight": "голод", "accent": ACC},
}
TL = {
    "id": "arch_j2", "type": "timeline", "composition": "TimelineJourney",
    "scene_id": "scene_094", "start": 610.0, "duration_sec": 13.0,
    "anchor": "в 2015 году суд Раджастхана приравнял саллекхану к самоубийству",
    "props": {
        "title": "Саллекхана: закон", "accent": ACC, "durationInFrames": 390,
        "events": [
            {"year": 2015, "label": "Раджастхан: запрет"},
            {"year": "ВС Индии", "label": "решение отменил"},
            {"year": "Сейчас", "label": "спор продолжается"},
        ],
    },
}

NEW = [CROWD, NET, KIN, TL]
DROP_IDS = {"ov_007"}  # слабый CountUpBar 300 → заменяем толпой


def main() -> int:
    rendered = render_overlays(NEW, PROJECT / "assets" / "arche3b", overwrite=True)
    if len(rendered) != len(NEW):
        print(f"ВНИМАНИЕ отрендерено {len(rendered)}/{len(NEW)}")

    manifest = PROJECT / "overlays_rendered.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    by_id = {o["id"]: o for o in data["overlays"] if o["id"] not in DROP_IDS}
    for r in rendered:
        by_id[r["id"]] = r
    data["overlays"] = sorted(by_id.values(), key=lambda o: o["start"])
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    seq = pymiere.objects.app.project.activeSequence
    v8 = seq.videoTracks[7]
    removed = 0
    for c in reversed(list(v8.clips)):
        if "ov_007" in c.name:
            c.remove(False, False); removed += 1
    print(f"снят ov_007: {removed}")

    n = place_overlays(seq, rendered, PROJECT.resolve(), track_idx=7)
    pymiere.objects.app.project.save()
    print(f"уложено {n}, всего оверлеев {len(data['overlays'])}, сохранено")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
