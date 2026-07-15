"""
services/overlays/evidence.py
Отдельный проход по ОТСЫЛКАМ на документальный материал: архивные кадры, фото с
мест, видеозаписи, документы, показания. Ставит рамку-плашку «АРХИВ»/«ФОТО»/
«ЗАПИСЬ»/«ДОКУМЕНТ» (EvidenceFrame — уголки видоискателя + rec-точка, тело
просвечивает = «это документальный кадр»).

Ключевой фильтр уместности: плашку ставим ТОЛЬКО если в закадре рядом реально
звучит слово-триггер отсылки (кадр/запись/фото/документ/показания/…), иначе LLM
легко «придумает» архив там, где его не показывают.
"""
from __future__ import annotations

from typing import Any, Dict, List

from core.logger import setup_logger
from services.llm.claude import ClaudeService
from services.overlays.detector import DETECT_MODEL, DUR, _resolve_start, _scene_rows

log = setup_logger("overlay_evidence")

# Слова-триггеры реальной отсылки на документальный материал.
TRIGGERS = (
    "кадр", "запис", "фото", "видео", "снят", "плёнк", "плен", "документ",
    "показан", "хроник", "архив", "сохранил", "свидетел",
)

SYSTEM = (
    "Ты — редактор документалки про секты. Находишь моменты, где закадр ПРЯМО "
    "ссылается на показанные ДОКУМЕНТАЛЬНЫЕ материалы: архивные кадры, фото с мест, "
    "видеозаписи, документы, показания. Только там, где это ЯВНО сказано."
)


def _has_trigger(words: List[dict], a: float, b: float) -> bool:
    seg = " ".join(
        str(w.get("word", "")) for w in words if a <= float(w.get("start", 0)) <= b
    ).lower()
    return any(t in seg for t in TRIGGERS)


def _build_prompt(rows: List[dict]) -> str:
    lines = [
        "Найди моменты-ССЫЛКИ на документальный материал. Плашка-рамка:",
        "«АРХИВ» / «ФОТО» / «ЗАПИСЬ» / «ДОКУМЕНТ».",
        'Формат СТРОГО JSON: {"ev":[{"scene_id","label":<АРХИВ|ФОТО|ЗАПИСЬ|ДОКУМЕНТ>,'
        '"sub":<≤4 слова, что за материал>,"anchor":<2-4 слова ДОСЛОВНО>}]}',
        "ТОЛЬКО явные отсылки («сохранилась запись», «на этих кадрах», «на фото»,",
        "«в документах», «показания свидетелей»). Не выдумывай. Бери только сильные.",
        "",
        "СЦЕНЫ ЗАКАДРА (id + текст):",
    ]
    for r in rows:
        lines.append(f'[{r["id"]}] {r["text"]}')
    return "\n".join(lines)


def detect_evidence(
    scenes: List[dict],
    alignment: dict,
    *,
    max_frames: int = 6,
    min_gap_sec: float = 40.0,
    model: str = DETECT_MODEL,
) -> Dict[str, Any]:
    """Возвращает {"overlays": [EvidenceFrame-оверлеи]} — рамки «АРХИВ», готовые к рендеру."""
    rows = _scene_rows(scenes, alignment)
    if not rows:
        log.warning("Нет пригодных сцен для поиска АРХИВ-отсылок")
        return {"overlays": []}
    words = alignment.get("words", []) or []
    rows_by = {r["id"]: r for r in rows}

    log.info(f"Ищу АРХИВ-отсылки по {len(rows)} сценам (model={model})...")
    llm = ClaudeService(model=model)
    data = llm.call_json(_build_prompt(rows), max_tokens=3000, temperature=0.1, system=SYSTEM)
    cand = data.get("ev", data) if isinstance(data, dict) else data
    if not isinstance(cand, list):
        log.warning("LLM вернул неожиданный формат — АРХИВ-плашек нет")
        return {"overlays": []}

    cand = [c for c in cand if c.get("scene_id") in rows_by]
    cand.sort(key=lambda c: rows_by[c["scene_id"]]["start"])

    out: List[dict] = []
    last = -1e9
    for c in cand:
        row = rows_by[c["scene_id"]]
        if not _has_trigger(words, row["start"] - 2, row["end"] + 2):
            log.info(f"  ✗ {row['id']} «{c.get('sub', '')}»: нет слова-триггера отсылки — пропуск")
            continue
        start = _resolve_start(c.get("anchor", ""), words, row["start"], row["end"], row["start"] + 0.3)
        if start - last < min_gap_sec:
            continue  # держим воздух между рамками
        last = start
        out.append({
            "id": f"ove_{len(out) + 1:02d}",
            "type": "evidence",
            "composition": "EvidenceFrame",
            "scene_id": c["scene_id"],
            "start": round(start, 2),
            "duration_sec": DUR["evidence"],
            "anchor": c.get("anchor", ""),
            "props": {"label": (c.get("label") or "АРХИВ"), "sub": c.get("sub", "")},
        })
        if len(out) >= max_frames:
            break

    log.info(f"АРХИВ: {len(out)} рамок-отсылок")
    return {"overlays": out}
