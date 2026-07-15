"""
services/overlays/archetypes.py
Детектор «сильных» полноэкранных приёмов нового поколения — где данность
становится образом. Пока 4 числовых типа (легко сверять с закадром):

  crowd     → CrowdPictograph   «X из Y» масс-жертвы (сетка фигурок)
  shock     → ShockCounter      шокирующий рост числа (тряска/вспышки)
  fill      → ProportionFill    процент/доля (сосуд заливается)
  timeline  → TimelineJourney   3–5 событий с годами (путь по хронологии)

Каждое число/год СВЕРЯЕТСЯ с закадром в окне сцены (уместность превыше всего) —
как в detector/names/evidence. Возвращает overlays с composition, готовые к
рендеру и укладке как полноэкранные сцены (в один список с cine).
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from core.logger import setup_logger
from services.llm.claude import ClaudeService
from services.overlays.detector import DETECT_MODEL, _num, _resolve_start, _scene_rows

log = setup_logger("overlay_archetypes")

COMPOSITION = {
    "crowd": "CrowdPictograph",
    "shock": "ShockCounter",
    "fill": "ProportionFill",
    "timeline": "TimelineJourney",
    "kinetic": "KineticType",
    "mapspread": "MapSpread",
    "network": "NetworkGraph",
}
DUR_FRAMES = {"crowd": 160, "shock": 150, "fill": 150, "kinetic": 130, "mapspread": 160, "network": 170}


def _tokens(s: str) -> List[str]:
    return re.sub(r"[^0-9а-яёa-z ]", " ", (s or "").lower()).split()


def _words_in(text: str, words: List[dict], a: float, b: float, need: int = 1) -> bool:
    """>= need значимых токенов (≥5 букв) из text реально звучат в окне."""
    seg = " ".join(str(w.get("word", "")) for w in words if a <= float(w.get("start", 0)) <= b).lower()
    hit = sum(1 for t in _tokens(text) if len(t) >= 5 and t in seg)
    return hit >= need


def _digits_in(v, words: List[dict], a: float, b: float) -> bool:
    """Число (или его «ядро» 40000→40) реально звучит в окне."""
    n = _num(v)
    if n is None:
        return False
    s = str(int(n))
    seg = " ".join(str(w.get("word", "")) for w in words if a <= float(w.get("start", 0)) <= b)
    nums = re.findall(r"\d+", seg)
    core = s.rstrip("0") or s
    return s in nums or (len(s) >= 4 and core in nums)


SYSTEM = (
    "Ты — режиссёр моушн-графики документалки про секты. Подбираешь МОЩНЫЙ "
    "полноэкранный приём ТОЛЬКО там, где данные реально сильные. Большинство мест "
    "не подходят. Числа/годы — строго реальные из текста, не выдумывай."
)


def _build_prompt(rows: List[dict], max_items: int) -> str:
    lines = [
        f"Найди до {max_items} сильных мест под ОДИН из приёмов. Формат JSON:",
        '{"items":[{...}]}. Каждый элемент — один из:',
        "",
        'A) {"type":"crowd","scene_id","total":<Y>,"filled":<X>,"label":<≤3 слова, что стало>,'
        '"sub":<место·год>,"anchor":...}',
        "   — масс-жертвы «X из Y» (X погибли/выжили). Y — сколько всего, X — сколько затронуто.",
        'B) {"type":"shock","scene_id","from":<обычно 0>,"to":<число>,"label":<≤3 слова>,'
        '"sub":<место·год>,"anchor":...}',
        "   — шокирующее число жертв (крутится вверх). Если «сначала A, потом B» — from=A, to=B.",
        'C) {"type":"fill","scene_id","percent":<0-100>,"label":<≤3 слова>,"sub":...,"anchor":...}',
        "   — процент/доля («87% не вернулись»).",
        'D) {"type":"timeline","scene_id","title":<≤4 слова>,"events":[{"year","label":<≤2 слова>}] (3-5),"anchor":...}',
        "   — хронология: 3–5 событий с ГОДАМИ, реально названными в тексте.",
        'E) {"type":"kinetic","scene_id","lines":[<строка1>,<строка2>],"highlight":<ключевое слово>,'
        '"anchor":...} — ХЛЁСТКАЯ фраза-вывод (2 строки, ≤6 слов). Слова — из смысла сцены.',
        'F) {"type":"mapspread","scene_id","title":<≤4 слова>,"label":<годы/подпись>,'
        '"places":[{"label","lat","lon"}] (2-5),"anchor":...} — как секта РАСПОЛЗАЛАСЬ/где очаги.',
        "   lat/lon реальные; места НАЗВАНЫ в тексте.",
        'G) {"type":"network","scene_id","title":<≤4 слова>,"leader":<кто во главе>,'
        '"roles":[<роль/звено ≤2 слова>] (3-5),"anchor":...} — СТРУКТУРА секты (лидер+звенья),',
        "   если в тексте описаны роли/иерархия.",
        "",
        "anchor — 2–5 слов ДОСЛОВНО из текста. Числа/годы/места — ТОЛЬКО реальные. РАЗНООБРАЗЬ типы —",
        "не давай один и тот же тип много раз, если подходит другой.",
        "",
        "СЦЕНЫ (id + текст):",
    ]
    for r in rows:
        lines.append(f'[{r["id"]}] {r["text"]}')
    return "\n".join(lines)


def detect_archetypes(
    scenes: List[dict],
    alignment: dict,
    *,
    max_items: int = 8,
    min_gap_sec: float = 40.0,
    model: str = DETECT_MODEL,
) -> Dict[str, Any]:
    """Возвращает {"overlays": [полноэкранные приёмы]}, числа сверены с закадром."""
    rows = _scene_rows(scenes, alignment)
    if not rows:
        return {"overlays": []}
    words = alignment.get("words", []) or []
    rows_by = {r["id"]: r for r in rows}

    log.info(f"Ищу мощные приёмы по {len(rows)} сценам (model={model})...")
    llm = ClaudeService(model=model)
    data = llm.call_json(_build_prompt(rows, max_items + 3), max_tokens=5000, temperature=0.15, system=SYSTEM)
    cand = data.get("items", data) if isinstance(data, dict) else data
    if not isinstance(cand, list):
        return {"overlays": []}
    cand = [c for c in cand if c.get("scene_id") in rows_by]
    cand.sort(key=lambda c: rows_by[c["scene_id"]]["start"])

    out: List[dict] = []
    last = -1e9
    for c in cand:
        typ = c.get("type")
        if typ not in COMPOSITION:
            continue
        row = rows_by[c["scene_id"]]
        a, b = row["start"] - 3, row["end"] + 4
        props: Dict[str, Any] = {}
        ok = False

        if typ == "crowd":
            total, filled = _num(c.get("total")), _num(c.get("filled"))
            if total and filled and 0 < filled <= total and _digits_in(total, words, a, b):
                props = {"total": int(total), "filled": int(filled), "label": c.get("label", ""), "sub": c.get("sub", "")}
                ok = True
        elif typ == "shock":
            to = _num(c.get("to"))
            if to and _digits_in(to, words, a, b):
                props = {"from": int(_num(c.get("from")) or 0), "to": int(to), "label": c.get("label", ""), "sub": c.get("sub", "")}
                ok = True
        elif typ == "fill":
            p = _num(c.get("percent"))
            if p is not None and 0 <= p <= 100 and _digits_in(p, words, a, b):
                props = {"percent": float(p), "label": c.get("label", ""), "sub": c.get("sub", "")}
                ok = True
        elif typ == "timeline":
            evs = []
            for e in c.get("events") or []:
                yr = str(e.get("year", "")).strip()
                lb = str(e.get("label", "")).strip()
                if yr and lb and _digits_in(yr, words, a, b):
                    evs.append({"year": yr, "label": lb})
            if len(evs) >= 3:
                props = {"title": c.get("title", ""), "events": evs[:5]}
                ok = True
        elif typ == "kinetic":
            lines = [str(x) for x in (c.get("lines") or []) if str(x).strip()][:3]
            if lines and _words_in(" ".join(lines) + " " + str(c.get("highlight", "")), words, a, b, need=1):
                props = {"lines": lines, "highlight": c.get("highlight", ""),
                         "stat": str(c.get("stat", "")), "statLabel": c.get("statLabel", "")}
                ok = True
        elif typ == "mapspread":
            places = []
            for p in c.get("places") or []:
                lat, lon = _num(p.get("lat")), _num(p.get("lon"))
                if p.get("label") and lat is not None and lon is not None and -90 <= lat <= 90 and -180 <= lon <= 180:
                    if _words_in(str(p["label"]), words, a, b, need=1):
                        places.append({"x": round((lon + 180) / 360 * 100, 2), "y": round((90 - lat) / 180 * 100, 2),
                                       "label": str(p["label"]), "grow": 300})
            if len(places) >= 2:
                props = {"title": c.get("title", ""), "label": c.get("label", ""), "origins": places[:5]}
                ok = True
        elif typ == "network":
            roles = [str(x) for x in (c.get("roles") or []) if str(x).strip()][:5]
            leader = str(c.get("leader", "")).strip()
            if leader and len(roles) >= 3 and _words_in(" ".join(roles) + " " + leader, words, a, b, need=1):
                from math import cos, pi, sin
                nodes = [{"label": leader, "x": 50, "y": 42, "hot": True}]
                for i, rl in enumerate(roles):
                    ang = 2 * pi * i / len(roles) - pi / 2
                    nodes.append({"label": rl, "x": round(50 + 30 * cos(ang), 1), "y": round(46 + 26 * sin(ang), 1)})
                edges = [[0, i + 1] for i in range(len(roles))]
                props = {"title": c.get("title", ""), "nodes": nodes, "edges": edges}
                ok = True

        if not ok:
            log.info(f"  ✗ {typ} @ {row['id']}: данные не сверились — пропуск")
            continue
        start = _resolve_start(c.get("anchor", ""), words, row["start"], row["end"], row["start"] + 0.3)
        if start - last < min_gap_sec:
            continue
        last = start
        frames = DUR_FRAMES.get(typ) or (50 + len(props.get("events", [])) * 55)
        out.append({
            "id": f"arch_{len(out) + 1:02d}",
            "type": typ,
            "composition": COMPOSITION[typ],
            "scene_id": c["scene_id"],
            "start": round(start, 2),
            "duration_sec": round(frames / 30, 2),
            "duration_frames": frames,
            "anchor": c.get("anchor", ""),
            "props": props,
        })
        if len(out) >= max_items:
            break

    log.info(f"Приёмы: {len(out)} ({', '.join(sorted({o['type'] for o in out}))})")
    return {"overlays": out}
