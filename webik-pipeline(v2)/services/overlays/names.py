"""
services/overlays/names.py
Отдельный проход по КЛЮЧЕВЫМ ПЕРСОНАМ — лидерам сект, основателям, организаторам.
Находит названные ПОЛНЫЕ имена, проверяет, что имя реально ЗВУЧИТ в закадре
(защита от выдумок), привязывает плашку к моменту первого упоминания.

Зачем отдельно: общий детектор (detector.py) намеренно скуп на тип name (кэп
1/уровень, «по минимуму»), поэтому лидеров, которых в ролике про секты много,
собираем специальным проходом с верификацией. Результат — NameLabel-оверлеи
(нижняя треть), формат совместим с overlays.json / рендер-мостом.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from core.logger import setup_logger
from services.llm.claude import ClaudeService
from services.overlays.detector import DETECT_MODEL, DUR, _resolve_start, _scene_rows

log = setup_logger("overlay_names")

SYSTEM = (
    "Ты — редактор документалки про секты и религиозный террор. Находишь КЛЮЧЕВЫХ "
    "названных ПЕРСОН — лидеров сект, основателей, организаторов. Только реальные "
    "ПОЛНЫЕ имена (имя+фамилия), ПРОИЗНЕСЁННЫЕ в тексте. Не клички, не выдумки."
)


def _norm(s: str) -> List[str]:
    return re.sub(r"[^а-яёa-z ]", " ", (s or "").lower()).split()


def _name_in_text(name: str, words: List[dict], a: float, b: float) -> bool:
    """Имя реально звучит в окне: хотя бы один значимый токен (≥4 букв) присутствует."""
    seg = " ".join(
        str(w.get("word", "")) for w in words if a <= float(w.get("start", 0)) <= b
    ).lower()
    return any(t in seg for t in _norm(name) if len(t) >= 4)


def _build_prompt(rows: List[dict]) -> str:
    lines = [
        "Для КАЖДОГО лидера/организатора/ключевой фигуры, названной в закадре, дай",
        "карточку-плашку.",
        'Формат СТРОГО JSON: {"names":[{"scene_id","name":<полное имя>,'
        '"sub":<роль · страна/год, ≤4 слова>,"anchor":<2-4 слова ДОСЛОВНО там, где',
        "имя звучит впервые>}]}",
        "Только ЛИДЕРЫ/организаторы/ключевые фигуры. НЕ клички, НЕ разговорные имена.",
        "Не выдумывай — только реально произнесённые полные имена. Один раз на персону.",
        "",
        "СЦЕНЫ ЗАКАДРА (id + текст):",
    ]
    for r in rows:
        lines.append(f'[{r["id"]}] {r["text"]}')
    return "\n".join(lines)


def detect_names(
    scenes: List[dict],
    alignment: dict,
    *,
    max_names: int = 14,
    min_gap_sec: float = 6.0,
    model: str = DETECT_MODEL,
) -> Dict[str, Any]:
    """Возвращает {"overlays": [NameLabel-оверлеи]} — плашки лидеров, готовые к рендеру."""
    rows = _scene_rows(scenes, alignment)
    if not rows:
        log.warning("Нет пригодных сцен для поиска имён")
        return {"overlays": []}
    words = alignment.get("words", []) or []
    rows_by = {r["id"]: r for r in rows}

    log.info(f"Ищу имена лидеров по {len(rows)} сценам (model={model})...")
    llm = ClaudeService(model=model)
    data = llm.call_json(_build_prompt(rows), max_tokens=4000, temperature=0.1, system=SYSTEM)
    cand = data.get("names", data) if isinstance(data, dict) else data
    if not isinstance(cand, list):
        log.warning("LLM вернул неожиданный формат — имён нет")
        return {"overlays": []}

    cand = [c for c in cand if c.get("scene_id") in rows_by]
    cand.sort(key=lambda c: rows_by[c["scene_id"]]["start"])

    out: List[dict] = []
    seen: set = set()
    last = -1e9
    for c in cand:
        nm = (c.get("name") or "").strip()
        key = " ".join(_norm(nm))
        if not nm or len(key) < 3 or key in seen:
            continue
        row = rows_by[c["scene_id"]]
        if not _name_in_text(nm, words, row["start"] - 2, row["end"] + 2):
            log.info(f"  ✗ {nm}: имя не звучит в закадре — пропуск")
            continue
        start = _resolve_start(c.get("anchor", ""), words, row["start"], row["end"], row["start"] + 0.3)
        if start - last < min_gap_sec:
            start = last + min_gap_sec
        seen.add(key)
        last = start
        out.append({
            "id": f"ovn_{len(out) + 1:02d}",
            "type": "name",
            "composition": "NameLabel",
            "scene_id": c["scene_id"],
            "start": round(start, 2),
            "duration_sec": DUR["name"],
            "anchor": c.get("anchor", ""),
            "props": {"name": nm, "sub": c.get("sub", "")},
        })
        if len(out) >= max_names:
            break

    log.info(f"Имена: {len(out)} плашек лидеров")
    return {"overlays": out}
