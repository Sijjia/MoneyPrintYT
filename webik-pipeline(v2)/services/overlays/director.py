"""
services/overlays/director.py
LLM-режиссёр кино-сцен (уровень B): находит в закадре СЕГМЕНТЫ из 2–4 связанных
данных, что складываются в одну мысль, и генерит спеку для Remotion-композиции
`Scene` — блоки в мире + путь камеры (наезд/панорама/облёт/отъезд-раскрытие).

Ключевое: тайминг привязан к РЕЧИ — камера приезжает к каждому блоку в момент,
когда о нём говорят (по пословному alignment). Длина сцены = длина сегмента
(уместность/сценарий, а не фикс).
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher
from math import asin, cos, radians, sin, sqrt
from typing import Any, Dict, List, Optional

from core.logger import setup_logger
from services.llm.claude import ClaudeService
from services.overlays.detector import DETECT_MODEL, _num, _scene_rows

log = setup_logger("scene_director")

FPS = 30

# --- Плотность/уместность ---
# Айдар любит ДЛИННЫЕ, дышащие сцены (у зашедшей сцены на 1:34 биты разнесены на
# ~11с — это хорошо). Поэтому span/gap мягкие: режем только патологию (мёртвый
# воздух 15с+ и разрыв сегмента 30с+). Настоящая проблема была не в длине бита, а
# в том, что сцены лепились ВПРИТЫК (сцена+глобус) — поэтому MIN_SCENE_GAP строгий.
SPAN_MAX = 30.0       # весь сегмент не длиннее — иначе это не единая мысль
GAP_MAX = 14.0        # соседние биты не дальше — иначе «мёртвый воздух» на кадре
PAIR_SPAN_MAX = 16.0  # пара (2 бита) должна быть кучнее тройки
MIN_SCENE_GAP = 45.0  # между концом одной кино-сцены и началом следующей (в т.ч. глобусом)

# Глобус — РЕДКИЙ приём (не на каждое упоминание места). Только реально «глобальный»
# разброс: ≥3 места, разнесённые по миру. Одна страна/город — это НЕ глобус.
GLOBE_CAP = 2          # максимум глобусов на весь ролик
GLOBE_MIN_PLACES = 3
GLOBE_MIN_SPREAD_KM = 2500.0


def _haversine_km(a: dict, b: dict) -> float:
    la1, lo1, la2, lo2 = map(radians, (a["lat"], a["lon"], b["lat"], b["lon"]))
    h = sin((la2 - la1) / 2) ** 2 + cos(la1) * cos(la2) * sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371.0 * asin(sqrt(h))


def _max_spread_km(places: List[dict]) -> float:
    return max((_haversine_km(places[i], places[j])
                for i in range(len(places)) for j in range(i + 1, len(places))), default=0.0)


def _norm(s: str) -> List[str]:
    return re.sub(r"[^0-9a-zа-яё ]", " ", (s or "").lower()).split()


def _time_of(
    anchor: str,
    words: List[dict],
    lo: Optional[float] = None,
    hi: Optional[float] = None,
) -> Optional[float]:
    """Поиск момента фразы-якоря в пословном alignment. None — слабо.

    Если заданы lo/hi — ищем ТОЛЬКО в этом окне (по времени слова). Это критично:
    иначе обобщённый якорь («погибло», «человек») цепляется где-то далеко по 27-мин
    ролику и биты одного сегмента разъезжаются на сотни секунд.
    """
    toks = _norm(anchor)
    if not toks or not words:
        return None
    if lo is not None or hi is not None:
        _lo = lo if lo is not None else -1e9
        _hi = hi if hi is not None else 1e9
        words = [w for w in words if _lo <= float(w.get("start", 0)) <= _hi]
        if not words:
            return None
    k = len(toks)
    target = " ".join(toks)
    best_r, best_t = 0.0, None
    for i in range(0, max(1, len(words) - k + 1)):
        win = words[i : i + k]
        cand = " ".join(_norm(" ".join(str(x.get("word", "")) for x in win)))
        r = SequenceMatcher(None, target, cand).ratio()
        if r > best_r:
            best_r, best_t = r, float(win[0].get("start", 0))
    # в окне сцены ложных совпадений почти нет → порог мягче
    thr = 0.5 if (lo is not None or hi is not None) else 0.6
    return best_t if best_r >= thr else None


SYSTEM = (
    "Ты — режиссёр моушн-графики документалки про культы и религиозный террор. "
    "Находишь в закадре СЕГМЕНТЫ, которые сильно смотрятся как отдельная кино-сцена: "
    "связка из 2–4 фактов/чисел, что ведут к ОДНОЙ мысли. Большинство сегментов НЕ "
    "подходят — бери только реально сильные, где данные складываются в историю."
)


def _build_prompt(rows: List[dict], max_scenes: int) -> str:
    lines = [
        f"Найди до {max_scenes} сильных кино-сегментов. Каждый — один из ДВУХ типов:",
        "",
        'A) "scene" — связка из 2–4 ДАННЫХ, что ведут к одной мысли.',
        '   поля: {"type":"scene","scene_id":<id сцены>,"headline":<вывод ≤5 слов>,"beats":[...]}.',
        "   Каждый бит — ОДИН из:",
        '     • {"kind":"stat","value":<полное число цифрами>,"label":<≤3 слова>,"anchor":...}',
        '     • {"kind":"bars","label":<заголовок ≤3 слова>,"items":[{"label","value"}...] (2-3),"anchor":...}',
        "         — только если в тексте реально СРАВНИВАЮТСЯ числа.",
        '     • {"kind":"ratio","filled":X,"total":Y,"label":<≤3 слова>,"anchor":...}',
        "         — только если в тексте «X из Y».",
        "",
        'B) "globe" — сегмент про ГЕОГРАФИЮ (перечислены страны/города событий).',
        '   поля: {"type":"globe","scene_id":<id сцены>,"title":<≤4 слова>,"places":[{"label","lat","lon"}...] (2-6),"anchor":...}.',
        "   lat/lon — реальные координаты. places — ТОЛЬКО страны/города, НАЗВАННЫЕ в",
        "   тексте этого сегмента. Не добавляй свои — если сказано «Россия, Африка,",
        "   Латинская Америка» — бери ровно их, не выдумывай Индию/Австралию.",
        "",
        "ГЛАВНОЕ ПРО ТАЙМИНГ:",
        "- scene_id — id сцены из списка, ГДЕ этот сегмент реально звучит (обязательно).",
        "- ВСЕ биты/anchor одного сегмента — из ОДНОЙ мысли, звучащей ПОДРЯД (в пределах",
        "  ~30 секунд, обычно одна сцена). НЕ собирай биты из разных концов ролика.",
        "- anchor — 2–5 слов ДОСЛОВНО из текста этой сцены, где звучит факт.",
        "Числа/места/факты — ТОЛЬКО реальные из текста, не выдумывай. Разнообразь типы битов.",
        "",
        'Ответ СТРОГО JSON: {"scenes":[{"type":"scene"|"globe","scene_id",...}]}.',
        "",
        "СЦЕНЫ ЗАКАДРА (id + текст):",
    ]
    for r in rows:
        lines.append(f'[{r["id"]}] {r["text"]}')
    return "\n".join(lines)


def _spread(n: int, center: float = 1500.0, gap: float = 820.0) -> List[float]:
    total = gap * (n - 1)
    return [center - total / 2 + i * gap for i in range(n)]


def _vspread(n: int, center: float = 640.0, gap: float = 300.0) -> List[float]:
    total = gap * (n - 1)
    return [center - total / 2 + i * gap for i in range(n)]


def _mk_block(bid: str, x: float, y: float, beat: dict) -> Dict[str, Any]:
    """Бит → блок сцены (bars/ratio/stat с фолбэком на stat)."""
    kind = beat.get("kind", "stat")
    blk: Dict[str, Any] = {"id": bid, "x": x, "y": y}
    if kind == "bars":
        items = []
        for it in beat.get("items") or []:
            v = _num(it.get("value"))
            if v is not None and it.get("label"):
                items.append({"label": str(it["label"]), "value": v})
        if len(items) >= 2:
            blk.update(kind="bars", items=items[:3], label=beat.get("label", ""))
            return blk
    elif kind == "ratio":
        fil, tot = _num(beat.get("filled")), _num(beat.get("total"))
        if fil and tot and tot > 0:
            blk.update(kind="ratio", filled=int(fil), total=int(tot), label=beat.get("label", ""))
            return blk
    blk.update(kind="stat", value=str(beat.get("value", "")), label=beat.get("label", ""),
               suffix=beat.get("suffix", ""))
    return blk


# Рецепты компоновки+камеры. Чередуются по сценам, чтобы не выглядело шаблонно.
# ВАЖНО: только КАМЕРА/компоновка — НЕ трогаем СМЫСЛ данных. Сравнительный бар-чарт
# делаем ТОЛЬКО когда сам LLM пометил числа как сравнимые (beat kind=bars); авто-склейка
# двух статов в бары запрещена — легко получить бред («3 года» vs «74 погибших»).
RECIPES = ["row", "column", "arc", "diagonal"]


def _positions(style: str, n: int):
    """(позиции блоков, позиция заголовка) под стиль."""
    if style == "column":
        ys = _vspread(n, 700, 300)
        return [(1500.0, y) for y in ys], (1500.0, ys[0] - 250)
    if style == "arc":
        xs = _spread(n, 1500, 760)
        ys = [640.0 + (130 if i % 2 else -70) for i in range(n)]
        return [(xs[i], ys[i]) for i in range(n)], (1500.0, 250)
    if style == "diagonal":
        xs, ys = _spread(n, 1500, 640), _vspread(n, 660, 200)
        return [(xs[i], ys[i]) for i in range(n)], (1500.0, 230)
    xs = _spread(n)  # row
    return [(x, 640.0) for x in xs], (1500.0, 300)


def _seq_scene(style: str, headline: str, timed: List[tuple]) -> Dict[str, Any]:
    """Последовательный проход камеры по битам с компоновкой стиля."""
    n = len(timed)
    t0 = timed[0][0]
    scene_start = max(0.0, t0 - 0.6)
    fbeats = [(round((t - scene_start) * FPS), b) for t, b in timed]
    pos, (hx, hy) = _positions(style, n)

    blocks = [_mk_block(f"b{i}", pos[i][0], pos[i][1], b) for i, (_, b) in enumerate(fbeats)]
    if headline:
        blocks.append({"id": "h", "kind": "headline", "x": hx, "y": hy, "text": headline})

    shots, prev_end = [], 0
    for i, (f, _) in enumerate(fbeats):
        move = max(8, f - prev_end)
        hold = max(10, int((fbeats[i + 1][0] - f) * 0.4)) if i < n - 1 else 55
        rotY = rotX = 0.0
        if style == "row":
            rotY = 8 if i % 2 == 0 else -8
        elif style == "column":
            rotX = 9.0
        elif style == "arc":
            rotY = -15 + 30 * (i / max(1, n - 1))     # облёт слева направо
        elif style == "diagonal":
            rotY, rotX = (11, 6) if i % 2 == 0 else (-11, -6)
        shots.append({"focus": f"b{i}", "zoom": 1.5, "move": move, "hold": hold,
                      "rotY": round(rotY, 1), "rotX": round(rotX, 1)})
        prev_end += move + hold

    pull_zoom = {"column": 0.66, "arc": 0.7, "diagonal": 0.68}.get(style, 0.72)
    pull_move, pull_hold = 75, 95
    shots.append({"focus": "h" if headline else "b0", "zoom": pull_zoom,
                  "move": pull_move, "hold": pull_hold, "rotY": 0.0, "rotX": 0.0})
    total = prev_end + pull_move + pull_hold + 24
    return {"composition": "Scene", "start": round(scene_start, 2),
            "duration_sec": round(total / FPS, 2), "duration_frames": total,
            "props": {"blocks": blocks, "shots": shots}}


def _build_scene(headline: str, timed: List[tuple], variant: int = 0) -> Optional[Dict[str, Any]]:
    """timed = [(t_sec, beat), ...] отсортировано. Строит спеку Scene по рецепту variant."""
    if len(timed) < 2:
        return None
    return _seq_scene(RECIPES[variant % len(RECIPES)], headline, timed)


def _build_globe(
    sc: dict, words: List[dict], lo: Optional[float] = None, hi: Optional[float] = None
) -> Optional[Dict[str, Any]]:
    """Гео-сегмент → 3D-глобус с пинами."""
    places = []
    for p in sc.get("places") or []:
        lat, lon = _num(p.get("lat")), _num(p.get("lon"))
        if p.get("label") and lat is not None and lon is not None \
                and -90 <= lat <= 90 and -180 <= lon <= 180:
            places.append({"label": str(p["label"]), "lat": lat, "lon": lon})
    if len(places) < GLOBE_MIN_PLACES:
        return None
    spread = _max_spread_km(places)
    if spread < GLOBE_MIN_SPREAD_KM:
        # одна страна/регион — не тянет на «глобус террора»
        return None
    t = _time_of(sc.get("anchor", ""), words, lo, hi)
    if t is None and lo is not None:
        t = lo + 0.3  # якорь не нашёлся — ставим в начало сцены (а не в 0!)
    start = max(0.0, (t if t is not None else 0.0) - 0.3)
    return {
        "composition": "Globe3D",
        "start": round(start, 2),
        "duration_sec": 10.0,
        "duration_frames": 300,
        "props": {"places": places[:6], "title": sc.get("title", "")},
    }


def direct_scenes(
    scenes: List[dict],
    alignment: dict,
    *,
    max_scenes: int = 2,
    model: str = DETECT_MODEL,
) -> Dict[str, Any]:
    """Возвращает {"scenes": [Scene-спеки]}."""
    rows = _scene_rows(scenes, alignment)
    if not rows:
        return {"scenes": []}
    words = alignment.get("words", []) or []
    # окно каждой сцены (+запас на соседние сцены — мысль может перетекать)
    win = {r["id"]: (r["start"], r["end"]) for r in rows}

    def _window(sc: dict):
        sid = sc.get("scene_id")
        if sid in win:
            lo, hi = win[sid]
            return lo - 6.0, hi + 30.0  # запас назад/вперёд на перетекание мысли
        return None, None

    log.info(f"Режиссёр: ищу кино-сегменты по {len(rows)} сценам (model={model})...")
    llm = ClaudeService(model=model)
    # просим с запасом — разведение по времени отберёт лучшие max_scenes
    data = llm.call_json(_build_prompt(rows, max_scenes + 3), max_tokens=8000, temperature=0.15, system=SYSTEM)
    raw = data.get("scenes", data) if isinstance(data, dict) else data
    if not isinstance(raw, list):
        return {"scenes": []}

    # 1) сначала собираем ВСЕХ кандидатов (с проверкой кучности битов)
    cands: List[Dict[str, Any]] = []
    for sc in raw:
        lo, hi = _window(sc)
        if sc.get("type") == "globe":
            spec = _build_globe(sc, words, lo, hi)
            if spec:
                cands.append(spec)
            continue

        beats = sc.get("beats") or []
        head = sc.get("headline", "")[:30]
        sid = sc.get("scene_id")
        # точные якоря по каждому биту (в окне сцены)
        anchored = {}
        for i, b in enumerate(beats):
            t = _time_of(b.get("anchor", ""), words, lo, hi)
            if t is not None:
                anchored[i] = t

        if len(anchored) == len(beats) and len(beats) >= 2:
            # идеал: все биты точно на слово (камера едет к цифре в момент речи)
            timed = sorted(((anchored[i], b) for i, b in enumerate(beats)), key=lambda x: x[0])
        elif sid in win and len(beats) >= 2:
            # якоря побились не все → раскидываем биты РОВНО по окну сцены (уместно по смыслу)
            ws, we = win[sid]
            dur = max(6.0, min(28.0, we - ws))
            n = len(beats)
            timed = [(ws + dur * (i + 0.5) / n, b) for i, b in enumerate(beats)]
            log.info(f"  «{head}»: якоря частичны ({len(anchored)}/{n}) → раскидал по окну {sid}")
        else:
            timed = sorted(((anchored[i], beats[i]) for i in anchored), key=lambda x: x[0])
        if len(timed) < 2:
            log.warning(f"  сегмент «{head}»: <2 битов (scene_id={sid} нет в окнах) — пропуск")
            continue
        timed.sort(key=lambda x: x[0])
        span = timed[-1][0] - timed[0][0]
        max_gap = max(timed[i + 1][0] - timed[i][0] for i in range(len(timed) - 1))
        # кучность: весь сегмент короткий, соседние биты рядом, пара — особенно кучно
        if span > SPAN_MAX:
            log.warning(f"  сегмент «{head}»: биты растянуты на {span:.0f}s (>{SPAN_MAX:.0f}) — пропуск")
            continue
        if max_gap > GAP_MAX:
            log.warning(f"  сегмент «{head}»: дырка {max_gap:.0f}s между битами (>{GAP_MAX:.0f}) — пропуск")
            continue
        if len(timed) == 2 and span > PAIR_SPAN_MAX:
            log.warning(f"  сегмент «{head}»: пара растянута на {span:.0f}s (>{PAIR_SPAN_MAX:.0f}) — пропуск")
            continue
        spec = _build_scene(sc.get("headline", ""), timed)
        if spec:
            spec["_nbeats"] = len(timed)
            spec["_timed"] = timed                      # для пересборки рецепта по порядку
            spec["_headline"] = sc.get("headline", "")
            cands.append(spec)

    # 2) разводим по времени: сортируем по силе (больше битов → важнее),
    #    берём жадно, отбрасывая тех, кто ближе MIN_SCENE_GAP к уже взятой сцене.
    #    сюжетные сцены (много битов) важнее глобусов; глобус = _nbeats 0 → в хвост.
    for s in cands:
        if s["composition"] == "Globe3D":
            s["_nbeats"] = 0
    cands.sort(key=lambda s: (-(s.get("_nbeats", 2)), s["start"]))
    kept: List[Dict[str, Any]] = []
    globes = 0
    for spec in cands:
        is_globe = spec["composition"] == "Globe3D"
        if is_globe and globes >= GLOBE_CAP:
            continue  # глобус — редкий приём, лимит исчерпан
        s0, s1 = spec["start"], spec["start"] + spec["duration_sec"]
        clash = any(not (s1 + MIN_SCENE_GAP <= k["start"] or s0 >= k["start"] + k["duration_sec"] + MIN_SCENE_GAP)
                    for k in kept)
        if clash:
            log.warning(f"  сцена @ {spec['start']}s впритык к другой (<{MIN_SCENE_GAP:.0f}s) — пропуск")
            continue
        kept.append(spec)
        if is_globe:
            globes += 1
        if len(kept) >= max_scenes:
            break

    kept.sort(key=lambda s: s["start"])
    out = []
    variant = 0  # чередуем рецепты по ПОРЯДКУ на таймлайне → соседи не похожи
    for spec in kept:
        spec.pop("_nbeats", None)
        if spec["composition"] == "Scene":
            # пересобираем сцену под рецепт её позиции (сохраняя старт/тайминг)
            timed, head = spec.pop("_timed"), spec.pop("_headline")
            rebuilt = _build_scene(head, timed, variant=variant)
            if rebuilt:
                rebuilt["start"] = spec["start"]  # старт уже зафиксирован (мог сдвигаться)
                spec = rebuilt
            variant += 1
        spec.pop("_timed", None)
        spec.pop("_headline", None)
        spec["id"] = f"cine_{len(out) + 1:02d}"
        out.append(spec)
        if spec["composition"] == "Globe3D":
            log.info(f"  глобус {spec['id']} @ {spec['start']}s, {len(spec['props']['places'])} мест")
        else:
            recipe = RECIPES[(variant - 1) % len(RECIPES)]
            kinds = [b.get("kind") for b in spec["props"]["blocks"]]
            log.info(f"  сцена {spec['id']} @ {spec['start']}s [{recipe}] {kinds}")

    log.info(f"Режиссёр: {len(out)} кино-сцен(ы) из {len(cands)} кандидатов")
    return {"scenes": out}
