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
from typing import Any, Dict, List, Optional

from core.logger import setup_logger
from services.llm.claude import ClaudeService
from services.overlays.detector import DETECT_MODEL, _scene_rows

log = setup_logger("scene_director")

FPS = 30


def _norm(s: str) -> List[str]:
    return re.sub(r"[^0-9a-zа-яё ]", " ", (s or "").lower()).split()


def _time_of(anchor: str, words: List[dict]) -> Optional[float]:
    """Глобальный поиск момента фразы-якоря в пословном alignment. None — слабо."""
    toks = _norm(anchor)
    if not toks or not words:
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
    return best_t if best_r >= 0.6 else None


SYSTEM = (
    "Ты — режиссёр моушн-графики документалки про культы и религиозный террор. "
    "Находишь в закадре СЕГМЕНТЫ, которые сильно смотрятся как отдельная кино-сцена: "
    "связка из 2–4 фактов/чисел, что ведут к ОДНОЙ мысли. Большинство сегментов НЕ "
    "подходят — бери только реально сильные, где данные складываются в историю."
)


def _build_prompt(rows: List[dict], max_scenes: int) -> str:
    lines = [
        f"Найди до {max_scenes} кино-сегментов. Для каждого верни 2–4 «бита» (факт/число",
        "с короткой подписью) и общую шапку-вывод. Биты — в порядке появления в тексте.",
        "",
        "Для КАЖДОГО бита обязателен anchor — 2–5 слов ДОСЛОВНО из текста, где он звучит",
        "(по нему привяжу тайминг камеры к речи).",
        "value — ПОЛНОЕ число цифрами (или короткий текст), label — ≤3 слова.",
        "",
        'Ответ СТРОГО JSON: {"scenes":[{"headline":"...","beats":[{"value","label","anchor"}]}]}.',
        "Факты и числа — только реальные из текста, не выдумывай.",
        "",
        "СЦЕНЫ ЗАКАДРА:",
    ]
    for r in rows:
        lines.append(f'[{r["id"]}] {r["text"]}')
    return "\n".join(lines)


def _spread(n: int) -> List[float]:
    """X-координаты n блоков в мире, по центру ~1500."""
    gap = 820
    total = gap * (n - 1)
    x0 = 1500 - total / 2
    return [x0 + i * gap for i in range(n)]


def _build_scene(headline: str, timed: List[tuple]) -> Optional[Dict[str, Any]]:
    """timed = [(t_sec, beat), ...] отсортировано. Строит спеку Scene."""
    n = len(timed)
    if n < 2:
        return None
    t0 = timed[0][0]
    scene_start = max(0.0, t0 - 0.6)
    fbeats = [(round((t - scene_start) * FPS), b) for t, b in timed]

    xs = _spread(n)
    blocks = []
    for i, (_, b) in enumerate(fbeats):
        blocks.append({
            "id": f"b{i}",
            "kind": "stat",
            "x": xs[i],
            "y": 640,
            "value": str(b.get("value", "")),
            "label": b.get("label", ""),
        })
    cx = sum(xs) / n
    if headline:
        blocks.append({"id": "h", "kind": "headline", "x": cx, "y": 300, "text": headline})

    # остановки: камера приезжает к биту i ровно на его кадре (moveEnd = f_i)
    shots = []
    prev_end = 0
    for i, (f, _) in enumerate(fbeats):
        move = max(8, f - prev_end)
        if i < n - 1:
            gap = fbeats[i + 1][0] - f
            hold = max(10, int(gap * 0.4))
        else:
            hold = 55
        shots.append({
            "focus": f"b{i}",
            "zoom": 1.5,
            "move": move,
            "hold": hold,
            "rotY": 8 if i % 2 == 0 else -8,  # облёт то влево, то вправо
        })
        prev_end += move + hold

    # финальный отъезд-раскрытие всех битов + шапки
    pull_move, pull_hold = 75, 95
    shots.append({
        "focus": "h" if headline else "b0",
        "zoom": 0.72,
        "move": pull_move,
        "hold": pull_hold,
        "rotY": 0,
    })
    total_frames = prev_end + pull_move + pull_hold + 24

    return {
        "composition": "Scene",
        "start": round(scene_start, 2),
        "duration_sec": round(total_frames / FPS, 2),
        "duration_frames": total_frames,
        "props": {"blocks": blocks, "shots": shots},
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

    log.info(f"Режиссёр: ищу кино-сегменты по {len(rows)} сценам (model={model})...")
    llm = ClaudeService(model=model)
    data = llm.call_json(_build_prompt(rows, max_scenes), max_tokens=6000, temperature=0.15, system=SYSTEM)
    raw = data.get("scenes", data) if isinstance(data, dict) else data
    if not isinstance(raw, list):
        return {"scenes": []}

    out = []
    for sc in raw[:max_scenes]:
        beats = sc.get("beats") or []
        timed = []
        for b in beats:
            t = _time_of(b.get("anchor", ""), words)
            if t is not None:
                timed.append((t, b))
        if len(timed) < 2:
            log.warning(f"  сегмент «{sc.get('headline','')[:30]}»: <2 битов привязано — пропуск")
            continue
        timed.sort(key=lambda x: x[0])
        span = timed[-1][0] - timed[0][0]
        if span > 35.0:
            log.warning(
                f"  сегмент «{sc.get('headline','')[:30]}»: биты растянуты на {span:.0f}s "
                f"(не единый сегмент) — пропуск"
            )
            continue
        spec = _build_scene(sc.get("headline", ""), timed)
        if spec:
            spec["id"] = f"cine_{len(out) + 1:02d}"
            out.append(spec)
            log.info(
                f"  сцена {spec['id']} @ {spec['start']}s, {spec['duration_sec']}s, "
                f"{len(timed)} битов: {[b.get('value') for _, b in timed]}"
            )

    log.info(f"Режиссёр: {len(out)} кино-сцен(ы)")
    return {"scenes": out}
