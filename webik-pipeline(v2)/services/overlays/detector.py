"""
services/overlays/detector.py
LLM-детектор моментов для динамических оверлеев (StatPop / NameLabel / KineticPhrase).

Сканит voiceover'ы сцен (scenes.json) + тайминги (alignment.json), просит дешёвую
LLM выбрать ТОЛЬКО сильные моменты и классифицировать их в один из трёх типов
графики. Затем жёстко ограничивает плотность (макс на уровень + мин. зазор), чтобы
не перегружать ролик. Результат — overlays.json, который потом рендерит рендер-мост
и раскладывает Premiere-placer.

Ключевой принцип (Айдар): графика НЕ на каждом шагу — только на реально ударных
точках, с воздухом между ними.
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

from core.logger import setup_logger
from services.llm.claude import ClaudeService

log = setup_logger("overlay_detector")

# Дешёвая модель на механику (см. decision_cheap_model_mechanics).
DETECT_MODEL = "google/gemini-2.5-flash"

# Длительность оверлея по типу (сек).
DUR = {"stat": 3.7, "name": 3.7, "phrase": 4.0}

# Композиция Remotion по типу.
COMPOSITION = {"stat": "StatPop", "name": "NameLabel", "phrase": "KineticPhrase"}

# Небольшая задержка появления после старта сцены.
START_OFFSET = 0.3


def _scene_rows(scenes: List[dict], alignment: dict) -> List[dict]:
    """[{id, level, start, end, text}] — только озвученные и привязанные сцены."""
    asc = alignment.get("scenes", {})
    rows = []
    for s in scenes:
        sid = s["id"]
        vo = (s.get("voiceover") or "").strip()
        a = asc.get(sid) if isinstance(asc, dict) else None
        if not vo or not a:
            continue
        start = a.get("start")
        end = a.get("end")
        if start in (None, 0.0) or end in (None, 0.0) or end <= start:
            continue
        # плашки уровней/тем не трогаем — на них своя графика, не оверлеи
        vtype = (s.get("visual") or {}).get("type", "")
        if vtype in ("level_card", "topic_card"):
            continue
        rows.append({
            "id": sid,
            "level": s.get("level", 0),
            "start": round(float(start), 2),
            "end": round(float(end), 2),
            "text": vo,
        })
    return rows


SYSTEM = (
    "Ты — арт-директор моушн-графики для русскоязычного документального YouTube-канала "
    "в тёмном формате «айсберг» про религиозный террор и культы. Твоя задача — выбрать "
    "в закадровом тексте ТОЛЬКО самые ударные моменты и усилить их анимированной "
    "графикой поверх кадра. Будь скупым: большинство сцен НЕ получают ничего. Перегруз "
    "графикой выглядит дёшево."
)


def _build_prompt(rows: List[dict], max_per_level: int) -> str:
    lines = [
        "Ниже — сцены закадра (id + текст). Выбери сильные моменты и классифицируй в один",
        "из ТРЁХ типов графики:",
        "",
        '1. "stat" — одна яркая ЦИФРА, прозвучавшая в тексте (число жертв, год, количество,',
        '   процент, сумма). Поля: value (только цифры, можно с разделителями), label',
        "   (≤4 слова — что считаем), suffix (опц. \"%\", \"+\").",
        '2. "name" — ключевой ЧЕЛОВЕК, МЕСТО или КУЛЬТ, который стоит подписать. Поля:',
        "   name (≤3 слова), sub (опц.: страна · год / роль, ≤3 слова).",
        '3. "phrase" — КОРОТКАЯ хлёсткая фраза (3–6 слов) из текста или плотно его',
        "   передающая, на драматичной точке. Поля: phrase (3–6 слов), highlight (массив",
        "   индексов слов для акцента, с 0, 0–2 слова).",
        "",
        "ВАЖНО — ЯКОРЬ ТАЙМИНГА:",
        '- Для КАЖДОГО оверлея добавь поле "anchor" — 2–5 слов, скопированных ДОСЛОВНО',
        "  из текста этой сцены, ровно в том месте, где произносится это число/имя/факт.",
        "  По ним я привяжу оверлей к точному моменту речи. Копируй буквально как в тексте",
        '  (напр. для «307» anchor = "трёхсот семи человек"; для имени — само имя как в тексте).',
        "",
        "ПРАВИЛА:",
        f"- Примерно 2–{max_per_level} оверлея на уровень, хорошо разнесённые по времени.",
        "- Не ставь графику на соседние сцены — оставляй воздух.",
        "- Ссылайся на существующий scene_id из списка.",
        "- value/name/phrase должны быть ВЕРНЫ содержанию этой сцены — не выдумывай факты.",
        "- Разнообразь типы (не только цифры).",
        '- Ответ — СТРОГО JSON: {"overlays":[{"scene_id","type","anchor", ...поля}]}. Без пояснений.',
        "",
        "СЦЕНЫ:",
    ]
    for r in rows:
        lines.append(f'[{r["id"]}] (ур.{r["level"]}) {r["text"]}')
    return "\n".join(lines)


def _norm_tokens(s: str) -> List[str]:
    return re.sub(r"[^0-9a-zа-яё ]", " ", (s or "").lower()).split()


def _resolve_start(
    anchor: str,
    words: List[dict],
    win_start: float,
    win_end: float,
    fallback: float,
) -> float:
    """Точный момент по якорю: fuzzy-ищем слова anchor среди whisper-слов в окне
    сцены (±1с). Возвращаем старт лучшего совпадения (чуть раньше — появиться к
    слову). Если совпадение слабое — fallback (старт сцены)."""
    toks = _norm_tokens(anchor)
    if not toks or not words:
        return fallback
    ww = [w for w in words if win_start - 1.0 <= float(w.get("start", 0)) <= win_end + 1.0]
    if not ww:
        return fallback
    k = max(1, len(toks))
    target = " ".join(toks)
    best_r, best_start = 0.0, None
    for i in range(0, max(1, len(ww) - k + 1)):
        window = ww[i : i + k]
        cand = " ".join(_norm_tokens(" ".join(str(x.get("word", "")) for x in window)))
        r = SequenceMatcher(None, target, cand).ratio()
        if r > best_r:
            best_r, best_start = r, float(window[0].get("start", fallback))
    if best_r >= 0.55 and best_start is not None:
        return round(max(0.0, best_start - 0.25), 2)
    return fallback


def _enforce_density(
    cues: List[dict],
    rows_by_id: Dict[str, dict],
    words: List[dict],
    max_per_level: int,
    min_gap_sec: float,
) -> List[dict]:
    """Резолвим точный тайминг по якорю, затем лимит плотности: сортируем по
    времени, жадно оставляем с зазором, капим на уровень."""
    valid = []
    for c in cues:
        sid = c.get("scene_id")
        typ = c.get("type")
        row = rows_by_id.get(sid)
        if row is None or typ not in COMPOSITION:
            log.warning(f"  пропуск куля: неизвестный scene_id/type ({sid}/{typ})")
            continue
        c = dict(c)
        fallback = row["start"] + START_OFFSET
        c["_start"] = _resolve_start(
            c.get("anchor", ""), words, row["start"], row["end"], fallback
        )
        c["_level"] = row["level"]
        valid.append(c)

    valid.sort(key=lambda c: c["_start"])

    accepted: List[dict] = []
    per_level: Dict[int, int] = {}
    last_start = -1e9
    for c in valid:
        if c["_start"] - last_start < min_gap_sec:
            continue
        lvl = c["_level"]
        if per_level.get(lvl, 0) >= max_per_level:
            continue
        accepted.append(c)
        per_level[lvl] = per_level.get(lvl, 0) + 1
        last_start = c["_start"]
    return accepted


def detect_overlays(
    scenes: List[dict],
    alignment: dict,
    *,
    max_per_level: int = 4,
    min_gap_sec: float = 12.0,
    model: str = DETECT_MODEL,
) -> Dict[str, Any]:
    """Главный вход. Возвращает {"overlays": [...]} готовый к рендеру."""
    rows = _scene_rows(scenes, alignment)
    if not rows:
        log.warning("Нет пригодных сцен для детекции оверлеев")
        return {"overlays": []}
    rows_by_id = {r["id"]: r for r in rows}

    log.info(f"Детектирую оверлеи по {len(rows)} сценам (model={model})...")
    llm = ClaudeService(model=model)
    prompt = _build_prompt(rows, max_per_level)
    data = llm.call_json(prompt, max_tokens=8000, temperature=0.4, system=SYSTEM)

    raw = data.get("overlays", data) if isinstance(data, dict) else data
    if not isinstance(raw, list):
        log.warning("LLM вернул неожиданный формат — оверлеев нет")
        return {"overlays": []}
    log.info(f"LLM предложил {len(raw)} кулей, привязываю тайминг + лимит плотности...")

    words = alignment.get("words", []) or []
    accepted = _enforce_density(raw, rows_by_id, words, max_per_level, min_gap_sec)

    overlays = []
    for i, c in enumerate(accepted, 1):
        typ = c["type"]
        ov = {
            "id": f"ov_{i:03d}",
            "type": typ,
            "composition": COMPOSITION[typ],
            "scene_id": c["scene_id"],
            "anchor": c.get("anchor", ""),
            "start": round(c["_start"], 2),
            "duration_sec": DUR[typ],
        }
        if typ == "stat":
            value = str(c.get("value", "")).strip()
            suffix = str(c.get("suffix", "")).strip()
            # хвостовой + или % переносим в suffix, чтобы счётчик их не съел
            if value and value[-1] in "+%" and not suffix:
                suffix = value[-1]
                value = value[:-1].strip()
            ov["props"] = {"value": value, "label": c.get("label", ""), "suffix": suffix}
        elif typ == "name":
            ov["props"] = {"name": c.get("name", ""), "sub": c.get("sub", "")}
        else:  # phrase
            # акцент максимум на 2 словах — иначе теряется смысл хайлайта
            hl = [int(x) for x in (c.get("highlight") or []) if isinstance(x, (int, float))]
            phrase = c.get("phrase", "")
            n_words = len(phrase.split())
            if len(hl) > 2 or (n_words and len(hl) >= n_words):
                hl = hl[:2]
            ov["props"] = {"phrase": phrase, "highlight": hl}
        overlays.append(ov)

    by_level: Dict[int, int] = {}
    for c in accepted:
        by_level[c["_level"]] = by_level.get(c["_level"], 0) + 1
    log.info(f"Принято {len(overlays)} оверлеев. По уровням: {dict(sorted(by_level.items()))}")
    return {"overlays": overlays, "model": model, "n_scenes": len(rows)}
