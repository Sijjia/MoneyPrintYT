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
        "Ты — режиссёр монтажа YouTube-канала в док-стиле. Подбираешь ИЛЛЮСТРАТИВНЫЕ "
        "вставки-сцены: под конкретную сцену закадра берёшь ОДИН короткий момент из "
        "аниме / фильма / мультика, который по СМЫСЛУ и картинке точно ложится на эту "
        "сцену и делает её ярче. Не мем-реакция, а именно уместный киношный момент."
    )
    prompt = f"""Ролик «Айсберг религиозного террора» (секты, культы, мошенники, фанатики). Тема тяжёлая.

Ниже СЦЕНЫ закадра: индекс, id, время, уровень (L), длительность, текст. [ГРАФИКА] = там инфографика.

ЗАДАЧА: выбери {N_MIN}-{N_MAX} сцен, под каждую из которых ХОРОШО ложится ОДИН момент из
аниме/фильма/мультика — по смыслу и картинке. Одно медиа = одна сцена (можно охватить 2
соседние, если так лучше). Разные источники (не всё из одного фильма). Выборочно — только
там, где совпадение РЕАЛЬНО сильное, не притянутое.

ПРАВИЛА:
1. Клип должен ВИЗУАЛЬНО/по смыслу подходить сцене (образ, действие, атмосфера, метафора).
2. СТРОГО НЕЛЬЗЯ вставки на убийства/трупы/пытки/увечья/суицид/гибель (особенно детей);
   и сам клип без крови/резни. На таких сценах — пропусти.
3. НЕ бери сцены с пометкой [ГРАФИКА].
4. Распредели по ролику, не кучей.

Для каждой верни объект:
- idx: индекс сцены
- scene_id
- span: 1 (только эта сцена) или 2 (эта + следующая)
- source: "anime" | "movie" | "cartoon"
- idea: по-русски какой именно момент/сцена из какого произведения и почему ложится
- query: КОНКРЕТНЫЙ англ. запрос на ИМЕННО этот момент (название произведения + что показано + scene/clip).
  Нельзя "template","green screen","chroma".
- why: 1 фраза — как совпадает по смыслу

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
    for p in picks:
        idx = p.get("idx")
        if idx is None or idx not in by_idx:
            continue
        s = by_idx[idx]
        start = s["start"]
        end = s["end"]
        if p.get("span") == 2 and idx + 1 in by_idx:
            end = by_idx[idx + 1]["end"]
        p["start"] = round(start, 2)
        p["end"] = round(end, 2)
        p["dur"] = round(end - start, 2)
        p["scene_id"] = s["scene_id"]
        clean.append(p)

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
