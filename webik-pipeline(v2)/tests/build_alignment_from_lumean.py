"""Строит assets/alignment.json (тайминги сцен) из точного пословного alignment
Lumean (full.align.json) — последовательный проход по словам с ресинком на
паузах-якорях 1.5с после каждой темы (гасит дрейф токенизации).

Формат совместим с tests/assemble_religioznyj.py: {scenes:{sid:{start,end,n_words}},
words, duration}.
"""
import json
import re
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-"
GAP_ANCHOR = 1.4  # порог паузы-темы


def toks(s: str):
    return [w for w in re.split(r"\s+", (s or "").strip()) if w]


def main() -> int:
    al = json.loads((PROJECT / "assets" / "voice" / "full.align.json").read_text(encoding="utf-8"))
    words = al["words"]
    duration = float(al["duration_seconds"])
    sc = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))
    items = sc if isinstance(sc, list) else sc["scenes"]

    # индексы слов, ПЕРЕД которыми большой разрыв (пауза-тема) → сильные якоря
    gap_after = []  # word index i: gap перед words[i] >= порога → words[i] = первое слово после паузы
    for i in range(1, len(words)):
        if words[i]["start"] - words[i - 1]["end"] >= GAP_ANCHOR:
            gap_after.append(i)
    print(f"якорей-пауз найдено: {len(gap_after)} (тем-карточек в scenes: "
          f"{sum(1 for s in items if s.get('visual',{}).get('type')=='topic_card')})")

    scenes_out = {}
    p = 0            # указатель на текущее слово
    anchor_i = 0     # индекс следующего якоря
    for s in items:
        sid = s.get("id") or s.get("scene_id")
        vo = s.get("voiceover") or ""
        n = len(toks(vo))
        vtype = s.get("visual", {}).get("type")
        if n == 0:
            # сцена без озвучки — нулевой слот в текущей точке
            t = words[p]["start"] if p < len(words) else duration
            scenes_out[sid] = {"start": round(t, 3), "end": round(t, 3), "n_words": 0}
            continue
        p = min(p, len(words) - 1)
        start = words[p]["start"]
        end_idx = min(p + n - 1, len(words) - 1)
        end = words[end_idx]["end"]
        scenes_out[sid] = {"start": round(start, 3), "end": round(end, 3), "n_words": n}
        p = end_idx + 1
        # после ТЕМЫ — ресинк указателя на первое слово после ближайшей паузы-якоря
        if vtype == "topic_card" and anchor_i < len(gap_after):
            # берём якорь, ближайший к текущему p (пауза сразу после названия темы)
            while anchor_i < len(gap_after) and gap_after[anchor_i] < p - 2:
                anchor_i += 1
            if anchor_i < len(gap_after):
                # подвинуть конец темы на слово перед паузой, а указатель — на слово после
                gi = gap_after[anchor_i]
                scenes_out[sid]["end"] = round(words[gi - 1]["end"], 3)
                p = gi
                anchor_i += 1

    # монотонность + запись
    out = {
        "duration": duration,
        "method": "lumean-native",
        "language": "ru",
        "words": [{"word": w["word"], "start": w["start"], "end": w["end"]} for w in words],
        "scenes": scenes_out,
        "paused_at_levels": True,
    }
    (PROJECT / "assets" / "alignment.json").write_text(
        json.dumps(out, ensure_ascii=False), encoding="utf-8")

    # проверка монотонности стартов
    ordered = [(sid, v["start"], v["end"]) for sid, v in scenes_out.items() if v["n_words"] > 0]
    bad = sum(1 for i in range(1, len(ordered)) if ordered[i][1] < ordered[i - 1][1] - 0.5)
    print(f"scenes: {len(scenes_out)} | dur {duration:.1f}s | немонотонных стартов: {bad}")
    print(f"первая: {ordered[0]}  последняя: {ordered[-1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
