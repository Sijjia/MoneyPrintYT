"""СЕЛЕКТИВНО выбирает ~28-35 сильнейших моментов «Айсберг DreamWorks» и назначает
каждому ПРИЁМ графики из палитры. Остальное = живой футаж. Пишет graphics_plan_v2_dw.json."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.llm.claude import ClaudeService

PROJECT = ROOT / "projects" / "2026-08-25_aysberg-dreamworks-lost-media-i-temnaya-skrytaya-storona-stu"

SYSTEM = ("Ты — арт-режиссёр документалки про DreamWorks. Выбираешь ТОЧЕЧНО самые сильные моменты "
          "для графики и назначаешь каждому подходящий приём. Графика — акцент, не фон; большинство сцен без неё.")

RULES = """Ниже ВСЕ сцены (id, тема, текст). Выбери 28-35 САМЫХ СИЛЬНЫХ моментов под графику
(шок-факты, сравнения, потерянные/вырезанные фильмы, страшные культовые кадры, крупные цифры,
знаменитые цитаты, начала тем). Остальные НЕ бери — там останется живой футаж.

Каждому выбранному назначь ОДИН treatment и заполни нужные поля:
- "dossier"    — потерянный/убитый фильм. fields: title, subtitle, stamp(УНИЧТОЖЕН/ОТМЕНЁН/СТЁРТ/ПОТЕРЯН), meta[{k,v}]
- "cut_stamp"  — вырезанная сцена. fields: title, stamp="ВЫРЕЗАНО"
- "glitch"     — утёкший/повреждённый материал (ранние тесты, лики). fields: title, subtitle
- "terminated" — производство фильма оборвано. fields: title, subtitle
- "split"      — сравнение двух. fields: title, a{label,sub}, b{label,sub}
- "uncanny"    — жуткий ранний CGI (зловещая долина). fields: title, subtitle
- "timeline"   — хронология событий студии. fields: title, events[{year,text}]
- "money"      — крупные деньги/провал/увольнения. fields: title, number, label, sub
- "headline"   — новостной заголовок (увольнения, поглощение). fields: headline, source, date
- "drama_freeze" — драматизация страшного культового кадра. fields: title, subtitle
- "quote"      — знаменитая реплика. fields: text, author
- "filmstrip"  — показ футажа в киноленте (начало темы). fields: title, subtitle

Верни ТОЛЬКО JSON-массив объектов {id, treatment, ...поля...}. Текст полей по-русски, коротко, заглавными где уместно."""


def main() -> int:
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    outline = json.loads((PROJECT / "outline.json").read_text(encoding="utf-8"))
    id2t = {t["id"]: t["title"] for L in outline["levels"] for t in L["topics"]}
    body = [s for s in scenes if s.get("section") not in ("topic_card", "level_card")]
    lines = [f'{s["id"]}|{id2t.get(s.get("topic_id"),"")}|{(s.get("voiceover") or "")[:120]}'
             for s in body if (s.get("voiceover") or "").strip()]
    print(f"сцен на вход: {len(lines)}")

    llm = ClaudeService(model="anthropic/claude-sonnet-4.5")
    res = llm.call_json(RULES + "\n\nСЦЕНЫ:\n" + "\n".join(lines), max_tokens=14000, temperature=0.3, system=SYSTEM)
    if isinstance(res, dict): res = res.get("items") or res.get("picks") or res.get("scenes") or []
    plan = {r["id"]: r for r in res if r.get("id")}
    (PROJECT / "graphics_plan_v2_dw.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    import collections
    c = collections.Counter(v.get("treatment") for v in plan.values())
    print(f"\nВЫБРАНО: {len(plan)} моментов")
    for t, n in c.most_common(): print(f"  {t}: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
