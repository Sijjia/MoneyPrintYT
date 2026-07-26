"""Больше разной графики на бедные темы (Орден Храма/Китай/Colonia/Канунгу/
Альбиносы/Шакахола). Разные типы. Позиции по новому alignment. Аддитивно на V8.
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

NEW = [
    # Орден Храма — таймлайн волн смертей
    {"id": "arch_s1", "type": "timeline", "composition": "TimelineJourney", "scene_id": "scene_186",
     "start": 1409.0, "duration_sec": 15.0, "anchor": "октября тысяча девятьсот девяносто четвёртого года всё началось в Канаде",
     "props": {"title": "Орден Солнечного Храма", "accent": ACC, "durationInFrames": 450, "events": [
         {"year": "окт 1994", "label": "Канада: семья"},
         {"year": 1994, "label": "Швейцария: десятки"},
         {"year": "март 1997", "label": "Франция: последние 5"}]}},
    # Орден Храма — карта 3 стран
    {"id": "arch_s2", "type": "mapspread", "composition": "MapSpread", "scene_id": "scene_188",
     "start": 1425.0, "duration_sec": 9.0, "anchor": "Швейцарии Франции и Канаде",
     "props": {"title": "Швейцария · Франция · Канада", "label": "≈74 погибших · 1994–1997", "durationInFrames": 270, "accent": ACC,
               "origins": [{"x": 52.2, "y": 24.0}, {"x": 50.6, "y": 24.4}, {"x": 30.0, "y": 24.4}]}},
    # Китай — сеть тайных тюрем
    {"id": "arch_c1", "type": "network", "composition": "NetworkGraph", "scene_id": "scene_165",
     "start": 1151.0, "duration_sec": 11.0, "anchor": "тайные тюрьмы для членов запрещённых религиозных групп",
     "props": {"title": "Тайные «центры» · 2010–2023", "titleStart": 8, "durationInFrames": 330, "accent": ACC,
               "nodes": [{"label": "«Центры»", "x": 50, "y": 49, "hot": True},
                         {"label": "Фалуньгун", "x": 72, "y": 27}, {"label": "Христиане", "x": 72, "y": 71},
                         {"label": "Мусульмане", "x": 28, "y": 71}, {"label": "«Слишком верующие»", "x": 28, "y": 27}],
               "edges": [[0, 1], [0, 2], [0, 3], [0, 4]], "nodeStart": [4, 40, 78, 116, 154]}},
    # Китай — кинетик мишеней (по провинциям)
    {"id": "arch_c2", "type": "kinetic", "composition": "KineticType", "scene_id": "scene_164",
     "start": 1131.0, "duration_sec": 4.5, "anchor": "по провинциям Хэнань Аньхой Шаньдун",
     "props": {"lines": ["ХЭНАНЬ · АНЬХОЙ · ШАНЬДУН", "ПОДПОЛЬНЫЕ «ЦЕНТРЫ»"], "highlight": "центры", "accent": ACC}},
    # Colonia — таймлайн полувека
    {"id": "arch_cd", "type": "timeline", "composition": "TimelineJourney", "scene_id": "scene_175",
     "start": 1277.0, "duration_sec": 16.0, "anchor": "арестовали только в две тысячи пятом году",
     "props": {"title": "Colonia Dignidad", "accent": ACC, "durationInFrames": 480, "events": [
         {"year": 1961, "label": "Шефер основал"},
         {"year": "Пиночет", "label": "DINA: центр пыток"},
         {"year": 2005, "label": "арест"},
         {"year": 2006, "label": "20 лет тюрьмы"}]}},
    # Канунгу — толпа 778
    {"id": "arch_k1", "type": "crowd", "composition": "CrowdPictograph", "scene_id": "scene_137",
     "start": 1090.0, "duration_sec": 5.3, "anchor": "около семисот семидесяти восьми погибших",
     "props": {"total": 778, "filled": 778, "label": "сожжены", "sub": "Канунгу · 2000", "accent": ACC}},
    # Альбиносы — карта Восточной Африки
    {"id": "arch_a1", "type": "mapspread", "composition": "MapSpread", "scene_id": "scene_177",
     "start": 1304.0, "duration_sec": 9.0, "anchor": "В Танзании Малави Бурунди",
     "props": {"title": "Танзания · Малави · Бурунди", "label": "Охота на альбиносов", "durationInFrames": 270, "accent": ACC,
               "origins": [{"x": 59.7, "y": 53.3}, {"x": 59.4, "y": 57.2}, {"x": 58.3, "y": 51.7}]}},
    # Шакахола — толпа 429
    {"id": "arch_sh", "type": "crowd", "composition": "CrowdPictograph", "scene_id": "scene_109",
     "start": 772.0, "duration_sec": 5.3, "anchor": "четыреста двадцать девять трупов",
     "props": {"total": 429, "filled": 429, "label": "погибли", "sub": "Шакахола · 2023", "accent": ACC}},
]


def main() -> int:
    rendered = render_overlays(NEW, PROJECT / "assets" / "arche3b", overwrite=True)
    print(f"отрендерено {len(rendered)}/{len(NEW)}")
    manifest = PROJECT / "overlays_rendered.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    by_id = {o["id"]: o for o in data["overlays"]}
    for r in rendered:
        by_id[r["id"]] = r
    data["overlays"] = sorted(by_id.values(), key=lambda o: o["start"])
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    seq = pymiere.objects.app.project.activeSequence
    n = place_overlays(seq, rendered, PROJECT.resolve(), track_idx=7)
    pymiere.objects.app.project.save()
    print(f"уложено {n}/{len(rendered)}, всего оверлеев {len(data['overlays'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
