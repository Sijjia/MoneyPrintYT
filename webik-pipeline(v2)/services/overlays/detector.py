"""
services/overlays/detector.py
LLM-детектор моментов для динамических оверлеев.

Сканит voiceover'ы сцен (scenes.json) + тайминги (alignment.json), просит дешёвую
LLM выбрать ТОЛЬКО сильные моменты, классифицировать их в подходящий ТИП графики
и дать якорь для точного тайминга. Затем привязывает оверлей к моменту речи
(fuzzy по пословному alignment) и жёстко ограничивает плотность (макс на уровень +
мин. зазор), чтобы не перегружать ролик. Результат — overlays.json.

Типы → композиции Remotion:
  stat     → StatPop          одиночное ударное число
  percent  → DonutProportion  процент/доля
  ratio    → Pictograph       «X из Y» (фигурки)
  compare  → BarCompare       сравнение 2–4 величин (только реальные числа!)
  name     → NameLabel        человек/место/культ (нижний третий)
  phrase   → KineticPhrase    короткая хлёсткая фраза
  evidence → EvidenceFrame    закадр ссылается на показанные кадры/фото/запись

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
DUR = {
    "stat": 3.7,
    "percent": 3.7,
    "ratio": 3.7,
    "compare": 4.5,
    "timeline": 5.0,
    "map": 5.0,
    "quote": 4.5,
    "spotlight": 3.5,
    "name": 3.7,
    "phrase": 4.0,
    "evidence": 3.5,
}

# Композиция Remotion по типу. stat → CountUpBar (число как мера-чарт, а не
# плоский текст — больше графики).
COMPOSITION = {
    "stat": "CountUpBar",
    "percent": "DonutProportion",
    "ratio": "Pictograph",
    "compare": "BarCompare",
    "timeline": "Timeline",
    "map": "MapPins",
    "quote": "QuoteCard",
    "spotlight": "Spotlight",
    "name": "NameLabel",
    "phrase": "KineticPhrase",
    "evidence": "EvidenceFrame",
}

# Небольшая задержка появления после старта сцены (fallback, если якорь не нашёлся).
START_OFFSET = 0.3


def _num(x: Any, default: Optional[float] = None) -> Optional[float]:
    """Достаёт число из int/float/строки ('75 000', '87%')."""
    if isinstance(x, (int, float)):
        return float(x)
    m = re.search(r"-?\d[\d\s]*", str(x or ""))
    return float(m.group().replace(" ", "")) if m else default


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
    "графикой выглядит дёшево. Для каждого момента выбери НАИБОЛЕЕ ПОДХОДЯЩИЙ тип."
)


def _build_prompt(rows: List[dict], max_per_level: int) -> str:
    lines = [
        "Ниже — сцены закадра (id + текст). Выбери сильные моменты и подбери каждому",
        "ПОДХОДЯЩИЙ тип графики:",
        "",
        '• "stat" — одно ударное ЧИСЛО (жертвы, год, сумма, количество).',
        "     value = ПОЛНОЕ число цифрами («7 000 000», не «7»; «75 000», не «75»).",
        "     НЕ сокращай словами (никаких «млн/тыс» в value). label (≤4 слова).",
        '     suffix — ТОЛЬКО символ: «%», «₽», «$». «+» добавляй лишь если в тексте',
        "     «более/свыше/около/до».",
        '• "percent" — ПРОЦЕНТ/доля («87% не вернулись»).',
        "     поля: percent (0–100), label (≤4 слова).",
        '• "ratio" — соотношение «X из Y» (X,Y небольшие, Y≤20).',
        "     поля: filled (X), total (Y), label (≤4 слова).",
        '• "compare" — СРАВНЕНИЕ 2–4 величин. ТОЛЬКО если в тексте реально названо',
        "     несколько сопоставимых чисел — НЕ выдумывай значения.",
        "     поля: title (≤4 слова), items:[{label,value}, ...] (2–4 шт).",
        '• "timeline" — ХРОНОЛОГИЯ: 2–5 событий с годами (если в тексте перечислены',
        "     годы/даты событий). поля: title (≤4 слова), events:[{year,label}] —",
        "     label ≤2 слова. Годы и события — только реальные из текста.",
        '• "map" — КАРТА С ПИНАМИ: 2–6 географических мест (если в тексте',
        "     перечислены СТРАНЫ/ГОРОДА событий). поля: title (≤4 слова),",
        "     places:[{label, lat, lon}] — lat/lon реальные координаты места",
        "     (широта -90..90, долгота -180..180). Только реальные места из текста.",
        '• "name" — ключевой ЧЕЛОВЕК/МЕСТО/КУЛЬТ. name = ПОЛНОЕ имя (имя+фамилия)',
        "     или официальное название; НЕ клички/прозвища/одиночные разговорные",
        "     имена (не «Кузя» — а «Пётр Кузнецов»). sub (опц. страна · год / роль).",
        '• "phrase" — КОРОТКАЯ хлёсткая фраза (3–6 слов). поля: phrase, highlight',
        "     (индексы 0–2 слов для акцента).",
        '• "evidence" — закадр ССЫЛАЕТСЯ на показанные кадры/фото/запись («на этих',
        "     кадрах видно…», «сохранилась запись», «на этом фото»). поля: label",
        "     (напр. «АРХИВ»/«ФОТО»/«ЗАПИСЬ»), sub (опц. год · место).",
        '• "quote" — ТОЛЬКО если в тексте есть ПРЯМАЯ цитата/высказывание конкретного',
        "     человека («он заявил…», «называл себя…», прямая речь). поля: text",
        "     (сама цитата, ≤10 слов), author (кто сказал).",
        '• "spotlight" — ТОЛЬКО если закадр ПРЯМО просит присмотреться к кадру',
        "     («обратите внимание», «посмотрите», «вот здесь»). поля: label (≤3 слова).",
        "",
        "ЯКОРЬ ТАЙМИНГА (обязательно для каждого):",
        '• "anchor" — 2–5 слов, скопированных ДОСЛОВНО из текста сцены, ровно там, где',
        "     звучит этот факт. По ним привяжу оверлей к точному моменту речи.",
        '     (напр. для «307» anchor = "около 307 человек").',
        "",
        "ПРАВИЛА:",
        "- УМЕСТНОСТЬ ПРЕВЫШЕ ВСЕГО: тип бери ТОЛЬКО если сцена реально ему",
        "  соответствует. Лучше не ставить оверлей, чем поставить неподходящий или",
        "  с выдуманными данными. Никогда не притягивай quote/spotlight/map/timeline",
        "  за уши — только когда условие типа явно выполнено.",
        "- ПЛОТНОСТЬ ВЫСОКАЯ: стремись к 2–3 графикам НА КАЖДУЮ ТЕМУ (не на уровень!).",
        f"  Уровень обычно = 4 темы → это ~8–{max_per_level} оверлеев на уровень. Почти",
        "  каждый заметный факт — число, процент, соотношение, год/дата, страна/город,",
        "  имя, сравнение, цитата — достоин своей графики. Не жадничай.",
        "- НО не в тупую: только там, где тип реально подходит содержанию (уместность).",
        "  Не лепи 2 графики в упор на соседние сцены, но между темами держи плотно.",
        "- РАВНОМЕРНОЕ ПОКРЫТИЕ (важно!): распределяй графику по ВСЕЙ длине темы, не кучкуй",
        "  в начале. НЕ оставляй участков длиннее ~40 секунд закадра без единой графики.",
        "  Если кусок повествовательный/эмоциональный и без чисел — всё равно поставь",
        "  уместную name/phrase/quote/evidence/spotlight по смыслу сказанного (имя учёного,",
        "  ключевая фраза, место, образ), чтобы не было пустых провалов.",
        "- Ссылайся на существующий scene_id из списка.",
        "- Значения ВЕРНЫ содержанию сцены — не выдумывай факты и числа.",
        "- РАЗНООБРАЗЬ типы внутри темы: не три stat подряд, а stat+timeline+name,",
        "  compare+map+quote и т.п. Активно используй timeline, map, percent, ratio,",
        "  compare, quote, evidence — а не только stat.",
        "- Активно ищи: проценты/доли → percent; «X из Y» → ratio; пары сопоставимых",
        "  чисел → compare; перечисления годов → timeline. Не выдумывай значения.",
        "- Не делай уровень из одинаковых типов — разнообразь графику.",
        '- Ответ — СТРОГО JSON: {"overlays":[{"scene_id","type","anchor", ...поля}]}.',
        "",
        "СЦЕНЫ:",
    ]
    for r in rows:
        lines.append(f'[{r["id"]}] (ур.{r["level"]}) {r["text"]}')
    return "\n".join(lines)


def _norm_tokens(s: str) -> List[str]:
    return re.sub(r"[^0-9a-zа-яё ]", " ", (s or "").lower()).split()


def _resolve_start(
    anchor: str, words: List[dict], win_start: float, win_end: float, fallback: float
) -> float:
    """Точный момент по якорю: fuzzy-ищем слова anchor среди whisper-слов в окне
    сцены (±1с). Возвращаем старт лучшего совпадения (чуть раньше). Слабое
    совпадение → fallback (старт сцены)."""
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
    type_caps: Dict[str, int],
) -> List[dict]:
    """Резолвим точный тайминг по якорю, затем лимит плотности + кэпы по типам."""
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
        c["_start"] = _resolve_start(c.get("anchor", ""), words, row["start"], row["end"], fallback)
        c["_level"] = row["level"]
        valid.append(c)

    valid.sort(key=lambda c: c["_start"])

    accepted: List[dict] = []
    per_level: Dict[int, int] = {}
    per_level_type: Dict[tuple, int] = {}
    last_start = -1e9
    for c in valid:
        if c["_start"] - last_start < min_gap_sec:
            continue
        lvl, typ = c["_level"], c["type"]
        if per_level.get(lvl, 0) >= max_per_level:
            continue
        # мягкий кэп по типу на уровень — держим баланс (имя ≤1, stat ≤2 и т.п.)
        cap = type_caps.get(typ)
        if cap is not None and per_level_type.get((lvl, typ), 0) >= cap:
            continue
        accepted.append(c)
        per_level[lvl] = per_level.get(lvl, 0) + 1
        per_level_type[(lvl, typ)] = per_level_type.get((lvl, typ), 0) + 1
        last_start = c["_start"]
    return accepted


def _build_props(c: dict) -> Optional[Dict[str, Any]]:
    """Строит props под нужный компонент. None → куль невалиден, пропустить."""
    typ = c["type"]
    if typ == "stat":
        value = str(c.get("value", "")).strip()
        suffix = str(c.get("suffix", "")).strip()
        if value and value[-1] in "+%" and not suffix:
            suffix, value = value[-1], value[:-1].strip()
        if not value:
            return None
        return {"value": value, "label": c.get("label", ""), "suffix": suffix}

    if typ == "percent":
        p = _num(c.get("percent"))
        if p is None:
            return None
        return {"percent": max(0.0, min(100.0, p)), "label": c.get("label", "")}

    if typ == "ratio":
        fil, tot = _num(c.get("filled")), _num(c.get("total"))
        if not fil or not tot or tot <= 0:
            return None
        return {"filled": int(fil), "total": int(tot), "label": c.get("label", "")}

    if typ == "compare":
        items = []
        for it in c.get("items") or []:
            v = _num(it.get("value"))
            if v is not None and it.get("label"):
                items.append({"label": str(it["label"]), "value": v})
        if len(items) < 2:
            return None
        return {"title": c.get("title", ""), "items": items[:4]}

    if typ == "timeline":
        events = []
        for e in c.get("events") or []:
            year = str(e.get("year", "")).strip()
            label = str(e.get("label", "")).strip()
            if year and label:
                events.append({"year": year, "label": label})
        if len(events) < 2:
            return None
        return {"title": c.get("title", ""), "events": events[:5]}

    if typ == "map":
        places = []
        for p in c.get("places") or []:
            lat, lon = _num(p.get("lat")), _num(p.get("lon"))
            if p.get("label") and lat is not None and lon is not None \
                    and -90 <= lat <= 90 and -180 <= lon <= 180:
                places.append({"label": str(p["label"]), "lat": lat, "lon": lon})
        if len(places) < 2:
            return None
        return {"title": c.get("title", ""), "places": places[:6]}

    if typ == "quote":
        text = str(c.get("text", "")).strip()
        if len(text.split()) < 2:
            return None
        return {"text": text, "author": c.get("author", "")}

    if typ == "spotlight":
        label = str(c.get("label", "")).strip()
        return {"label": label, "x": _num(c.get("x"), 50), "y": _num(c.get("y"), 48)}

    if typ == "name":
        if not c.get("name"):
            return None
        return {"name": c.get("name", ""), "sub": c.get("sub", "")}

    if typ == "phrase":
        phrase = c.get("phrase", "")
        if not phrase:
            return None
        hl = [int(x) for x in (c.get("highlight") or []) if isinstance(x, (int, float))]
        nw = len(phrase.split())
        if len(hl) > 2 or (nw and len(hl) >= nw):
            hl = hl[:2]
        return {"phrase": phrase, "highlight": hl}

    if typ == "evidence":
        return {"label": (c.get("label") or "АРХИВ"), "sub": c.get("sub", "")}

    return None


def detect_overlays(
    scenes: List[dict],
    alignment: dict,
    *,
    max_per_level: int = 4,
    min_gap_sec: float = 12.0,
    type_caps: Optional[Dict[str, int]] = None,
    model: str = DETECT_MODEL,
    system: str = SYSTEM,
) -> Dict[str, Any]:
    """Главный вход. Возвращает {"overlays": [...]} готовый к рендеру.

    type_caps — мягкий лимит на тип в пределах уровня (баланс микса).
    """
    if type_caps is None:
        type_caps = {"name": 1, "stat": 2}
    rows = _scene_rows(scenes, alignment)
    if not rows:
        log.warning("Нет пригодных сцен для детекции оверлеев")
        return {"overlays": []}
    rows_by_id = {r["id"]: r for r in rows}

    log.info(f"Детектирую оверлеи по {len(rows)} сценам (model={model})...")
    llm = ClaudeService(model=model)
    prompt = _build_prompt(rows, max_per_level)
    # низкая температура — стабильный набор между прогонами (меньше «пропаданий»)
    data = llm.call_json(prompt, max_tokens=16000, temperature=0.15, system=system)

    raw = data.get("overlays", data) if isinstance(data, dict) else data
    if not isinstance(raw, list):
        log.warning("LLM вернул неожиданный формат — оверлеев нет")
        return {"overlays": []}
    log.info(f"LLM предложил {len(raw)} кулей, привязываю тайминг + лимит плотности...")

    words = alignment.get("words", []) or []
    accepted = _enforce_density(
        raw, rows_by_id, words, max_per_level, min_gap_sec, type_caps
    )

    overlays = []
    by_type: Dict[str, int] = {}
    for c in accepted:
        props = _build_props(c)
        if props is None:
            log.warning(f"  {c['scene_id']} [{c['type']}]: невалидные поля — пропуск")
            continue
        typ = c["type"]
        overlays.append({
            "id": f"ov_{len(overlays) + 1:03d}",
            "type": typ,
            "composition": COMPOSITION[typ],
            "scene_id": c["scene_id"],
            "anchor": c.get("anchor", ""),
            "start": round(c["_start"], 2),
            "duration_sec": DUR[typ],
            "props": props,
        })
        by_type[typ] = by_type.get(typ, 0) + 1

    log.info(f"Принято {len(overlays)} оверлеев. По типам: {dict(sorted(by_type.items()))}")
    return {"overlays": overlays, "model": model, "n_scenes": len(rows)}
