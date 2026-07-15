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
}
DUR_FRAMES = {"crowd": 160, "shock": 150, "fill": 150}  # timeline — по числу событий


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
        "",
        "anchor — 2–5 слов ДОСЛОВНО из текста. Числа/годы — ТОЛЬКО реальные. Разнообразь типы.",
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
