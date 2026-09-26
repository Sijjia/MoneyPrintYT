"""Выбирает ~12-15 уместных КИНОВСТАВОК-отсылок: узнаваемые культовые моменты из самих мультов
DreamWorks как «винк»/мем по смыслу. НЕ над трагедией/цифрами/увольнениями. Пишет cutaways_dw.json."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.llm.claude import ClaudeService

PROJECT = ROOT / "projects" / "2026-08-25_aysberg-dreamworks-lost-media-i-temnaya-skrytaya-storona-stu"

SYSTEM = ("Ты — режиссёр монтажа документалки про DreamWorks. Точечно расставляешь короткие КИНОВСТАВКИ — "
          "узнаваемые культовые кадры из самих мультов DreamWorks — как отсылку/винк зрителю по смыслу текста. "
          "Это приправа, а не фон: только там, где момент реально в тему и тон это позволяет.")

RULES = """Ниже ВСЕ сцены (id | тема | текст). Выбери 12-15 моментов, куда идеально ложится
КОРОТКАЯ (1.5-3с) вставка узнаваемого культового кадра из мультика DreamWorks, о котором идёт речь
(или явно ассоциируемого), как отсылка/мем/винк.

ЖЁСТКО:
- Только КУЛЬТОВОЕ и УЗНАВАЕМОЕ (Шрек, Осёл, Кот в сапогах, По из Кунг-фу Панды, Алекс/Мадагаскар,
  Беззубик/Иккинг, Мегамозг, Синдбад и т.п.) — чтобы зритель сразу узнал.
- ПО СМЫСЛУ: кадр должен перекликаться с тем, что говорится в этот момент.
- НИКОГДА не над трагедией/страшным/цифрами/увольнениями/смертями/геноцидом — там вставки НЕ ставим.
- Не подряд; распределить по ролику. Не на сценах, где уже сильная графика по факту не помешает — можно, но не обязательно.

Для каждого верни объект:
{ "id": "scene_NNN",
  "film": "Шрек 2",
  "moment": "Кот в сапогах делает жалобные глаза",
  "query": "Puss in Boots big eyes Shrek 2 scene",   // точный поиск ЭТОГО кадра на YouTube (по-английски)
  "seconds": 2.2,                                       // 1.5-3.0
  "why": "в тексте про обаяние кота" }

Верни ТОЛЬКО JSON-массив таких объектов. Поля film/moment/why по-русски, query по-английски."""


def main() -> int:
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    outline = json.loads((PROJECT / "outline.json").read_text(encoding="utf-8"))
    id2t = {t["id"]: t["title"] for L in outline["levels"] for t in L["topics"]}
    body = [s for s in scenes if s.get("section") not in ("topic_card", "level_card")]
    lines = [f'{s["id"]}|{id2t.get(s.get("topic_id"),"")}|{(s.get("voiceover") or "")[:120]}'
             for s in body if (s.get("voiceover") or "").strip()]
    print(f"сцен на вход: {len(lines)}")

    llm = ClaudeService(model="anthropic/claude-sonnet-4.5")
    res = llm.call_json(RULES + "\n\nСЦЕНЫ:\n" + "\n".join(lines), max_tokens=8000, temperature=0.4, system=SYSTEM)
    if isinstance(res, dict): res = res.get("items") or res.get("cutaways") or res.get("picks") or []
    picks = [r for r in res if r.get("id") and r.get("query")]
    (PROJECT / "cutaways_dw.json").write_text(json.dumps(picks, ensure_ascii=False, indent=1), encoding="utf-8")
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    print(f"\nВЫБРАНО: {len(picks)} вставок")
    for r in sorted(picks, key=lambda x: al.get(x["id"], {}).get("start", 0)):
        t = al.get(r["id"], {}).get("start", 0)
        print(f"  {r['id']} @{t/60:.0f}:{t%60:02.0f}  {r.get('film')} — {r.get('moment')} [{r.get('seconds')}с]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
