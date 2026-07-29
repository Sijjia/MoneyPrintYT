"""Режиссёр сцен-вставок (V7-подход): по карте сцен (scene_map.json) выбирает
сцены, под которые ХОРОШО ложится момент из аниме/фильма/мультика ПО СМЫСЛУ —
одно медиа = одна сцена (иногда 2 соседние). Выборочно, из разных источников.

Вывод: <project>/v7_inserts.json — [{scene_id, span, query, source, idea, why}]
span = 1 или 2 (охватить эту сцену или её + следующую).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.llm.claude import ClaudeService

P = Path(__file__).resolve().parent.parent / "projects" / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-"
N_MIN, N_MAX = 12, 20


def mmss(s):
    return f"{int(s)//60:02d}:{int(s)%60:02d}"


def main() -> int:
    scenes = json.loads((P / "scene_map.json").read_text(encoding="utf-8"))
    lines = []
    for i, s in enumerate(scenes):
        if s["dur"] < 1.5:
            continue
        flag = " [ГРАФИКА]" if s["gfx"] else ""
        vo = (s["vo"] or "").replace("\n", " ").strip()
        if not vo:
            continue
        lines.append(f"[{i}] {s['scene_id']} {mmss(s['start'])} L{s['level']} {s['dur']:.1f}с{flag}: {vo}")
    transcript = "\n".join(lines)

    system = (
        "Ты — режиссёр монтажа популярного YouTube-канала. Подбираешь ИЛЛЮСТРАТИВНЫЕ "
        "вставки из КУЛЬТОВОЙ, ВСЕМ ИЗВЕСТНОЙ поп-культуры: под сцену закадра берёшь "
        "УЗНАВАЕМЫЙ момент из знаменитого фильма/сериала/аниме, который зритель мгновенно "
        "узнаёт («о, это же Во все тяжкие!»). Не безликий сток, а хиты, которые все видели."
    )
    prompt = f"""Ролик «Айсберг религиозного террора» (секты, культы, мошенники, фанатики). Тема тяжёлая.

Ниже СЦЕНЫ закадра: индекс, id, время, уровень (L), длительность, текст. [ГРАФИКА] = там инфографика.

ЗАДАЧА: выбери {N_MIN}-{N_MAX} сцен, под каждую подбери ОДИН КУЛЬТОВЫЙ, УЗНАВАЕМЫЙ момент из
популярного фильма/сериала/аниме, который по смыслу ложится на сцену.

ГЛАВНОЕ — «ВСЕМ ИЗВЕСТНОЕ»:
- Бери ЗНАМЕНИТЫЕ сцены, которые зритель узнаёт с ходу. Примеры соответствий:
  наркотики/варка → «Во все тяжкие» (Breaking Bad); большие деньги/жадность → «Волк с Уолл-стрит»,
  «Лицо со шрамом» (Scarface); мафия/власть → «Крёстный отец»; манипулятор/гений зла → «Джокер»,
  «Тетрадь смерти» (Death Note); культ/ритуал → «Солнцестояние» (Midsommar); безумие/фанатизм →
  «Бойцовский клуб»; толпа за лидером → «Игра престолов», «Властелин колец»; апокалипсис → известные блокбастеры.
- ПРЕДПОЧТЕНИЕ узнаваемому хиту, а не малоизвестному фильму.
- КАЖДЫЙ ИСТОЧНИК УНИКАЛЬНЫЙ — НЕ повторяй одно произведение дважды.

ДЛИНА: делай вставки ПОДЛИННЕЕ и со смысловой нагрузкой — span=2 или 3 (охватить 2-3 соседние
сцены), чтобы момент успел «прожиться». Короткие блипы не нужны.

ПРАВИЛА:
1. Момент должен по смыслу/картинке подходить сцене (образ, действие, атмосфера, метафора).
2. СТРОГО НЕЛЬЗЯ вставки на убийства/трупы/пытки/увечья/суицид/гибель (особенно детей);
   и сам клип без крови/резни. На таких сценах — пропусти.
3. НЕ бери сцены с пометкой [ГРАФИКА].
4. Распредели по ролику, не кучей.

Для каждой верни объект:
- idx: индекс сцены
- scene_id
- span: 2 или 3 (сколько соседних сцен охватить — для длины)
- source: "anime" | "movie" | "cartoon"
- title: название произведения (напр. "Breaking Bad")
- idea: по-русски какой именно культовый момент и почему ложится
- query: КОНКРЕТНЫЙ англ. запрос на ИМЕННО этот знаменитый момент (название + сцена + scene/clip),
  напр. "Breaking Bad I am the one who knocks scene", "Wolf of Wall Street money chest thump scene".
  Нельзя "template","green screen","chroma".
- why: 1 фраза — как совпадает по смыслу

Каждое произведение (title) — только ОДИН раз во всём ответе.
Верни ТОЛЬКО JSON-массив.

СЦЕНЫ:
{transcript}"""

    print(f"сцен передано: {len(lines)} | зову sonnet-режиссёра...")
    llm = ClaudeService()
    picks = llm.call_json(prompt, max_tokens=16000, temperature=0.8, system=system)
    if isinstance(picks, dict):
        picks = picks.get("items") or picks.get("inserts") or []

    by_idx = {i: s for i, s in enumerate(scenes)}
    clean = []
    seen_titles = set()
    for p in picks:
        idx = p.get("idx")
        if idx is None or idx not in by_idx:
            continue
        title = (p.get("title") or "").strip().lower()
        if title and title in seen_titles:   # дедуп источников — каждое произведение 1 раз
            continue
        s = by_idx[idx]
        start = s["start"]
        span = int(p.get("span", 2) or 2)
        end = s["end"]
        for k in range(1, span):             # охватить span соседних сцен для длины
            if idx + k in by_idx:
                end = by_idx[idx + k]["end"]
        dur = round(end - start, 2)
        if dur < 3.0:                         # слишком коротко — не берём
            continue
        p["start"] = round(start, 2)
        p["end"] = round(end, 2)
        p["dur"] = dur
        p["scene_id"] = s["scene_id"]
        clean.append(p)
        if title:
            seen_titles.add(title)

    (P / "v7_inserts.json").write_text(json.dumps({"inserts": clean}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n=== ВЫБРАНО {len(clean)} сцен-вставок ===")
    for c in clean:
        print(f"\n{mmss(c['start'])} {c['scene_id']} ({c['dur']:.1f}с) · {c.get('source')}")
        print(f"  идея:  {c.get('idea','')[:90]}")
        print(f"  запрос: {c.get('query','')}")
    print(f"\nсохранено → v7_inserts.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
