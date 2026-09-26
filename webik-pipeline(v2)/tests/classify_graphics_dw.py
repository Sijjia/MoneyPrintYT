"""Решает, каким видео-сценам DreamWorks нужна ГРАФИКА (обёртка футажа в архив-дизайн),
а какие оставить сырым футажём. Пишет graphics_plan_dw.json.
keep    — сильный узнаваемый киномомент (Волк-Смерть, казнь первенцев, геноцид панд…) → сырой футаж.
dossier — производственное/корпоративное/абстрактное/лост-медиа/слабый клип → CancelledDossier."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.llm.claude import ClaudeService

PROJECT = ROOT / "projects" / "2026-08-25_aysberg-dreamworks-lost-media-i-temnaya-skrytaya-storona-stu"
CHUNK = 26

SYSTEM = ("Ты — арт-директор документалки про DreamWorks. Решаешь, где показать сырой кадр из мультфильма, "
          "а где обернуть футаж в АРХИВНЫЙ дизайн (кино-монитор, целлулоид, штамп, метаданные-досье).")

RULES = """Для КАЖДОЙ видео-сцены верни {id, treatment, title, subtitle, stamp, meta}.

treatment:
- "keep" — сцена про КОНКРЕТНЫЙ УЗНАВАЕМЫЙ момент мультфильма, где кадр силён сам по себе
  (Волк-Смерть в Коте, десятая казнь в Принце Египта, геноцид панд в Кунг-фу Панде, потеря ноги Иккинга,
  Алекс видит стейки, зловещая долина/жуткий ранний CGI). Оставляем сырой футаж. Остальные поля пустые.
- "dossier" — сцена ПРОИЗВОДСТВЕННАЯ/корпоративная/абстрактная/про потерянный фильм/со слабым или общим
  футажём (Катценберг, суды с Disney, увольнения, крах студии 2014, отменённые B.O.O./Larrikins/Me and My
  Shadow, войны с кинотеатрами, «тёмная сторона студии», логотип). Оборачиваем в архив-досье.
  Для dossier заполни:
  - title: короткое НАЗВАНИЕ (фильм или субъект), напр. "B.O.O.", "LARRIKINS", "КАТЦЕНБЕРГ vs DISNEY", "КРАХ 2014".
  - subtitle: пояснение заглавными, 3-6 слов.
  - stamp: ТОЛЬКО для уничтоженных/потерянных фильмов/материалов — одно слово:
    "УНИЧТОЖЕН" / "ОТМЕНЁН" / "СТЁРТ" / "ПОТЕРЯН" / "ЗАСЕКРЕЧЕН". Иначе "".
  - meta: массив 2-3 объектов {k, v} — архивные факты (напр. {"k":"ГОД","v":"2015"}, {"k":"БЮДЖЕТ","v":"$60М"}).
    Значения короткие, заглавными. Числа как есть.

Верни ТОЛЬКО JSON-массив."""


def main() -> int:
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    man = json.loads((PROJECT / "assets" / "images" / "manifest.json").read_text(encoding="utf-8"))
    outline = json.loads((PROJECT / "outline.json").read_text(encoding="utf-8"))
    id2t = {t["id"]: t["title"] for L in outline["levels"] for t in L["topics"]}
    vids = [s for s in scenes if man.get(s["id"], {}).get("kind") == "video"]
    print(f"видео-сцен: {len(vids)}")

    llm = ClaudeService(model="google/gemini-2.5-flash")
    plan = {}
    for i in range(0, len(vids), CHUNK):
        ch = vids[i:i + CHUNK]
        lines = [f'{{"id":"{s["id"]}","topic":"{id2t.get(s.get("topic_id"),"")}",'
                 f'"vo":"{(s.get("voiceover") or "").replace(chr(34)," ")[:170]}"}}' for s in ch]
        try:
            res = llm.call_json(RULES + "\n\nСЦЕНЫ:\n" + "\n".join(lines), max_tokens=9000, temperature=0.2, system=SYSTEM)
            if isinstance(res, dict): res = res.get("items") or res.get("scenes") or []
            for r in res:
                if r.get("id"): plan[r["id"]] = r
        except Exception as e:
            print(f"  чанк {i//CHUNK+1}: {str(e)[:60]}")
        print(f"  {min(i+CHUNK,len(vids))}/{len(vids)}")

    (PROJECT / "graphics_plan_dw.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    import collections
    c = collections.Counter(v.get("treatment") for v in plan.values())
    st = sum(1 for v in plan.values() if v.get("stamp"))
    print(f"\nИТОГ: {dict(c)} | со штампом: {st} | всего {len(plan)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
