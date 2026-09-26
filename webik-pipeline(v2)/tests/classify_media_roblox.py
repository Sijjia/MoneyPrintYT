"""Классифицирует сцены «Айсберг Roblox» на корзины медиа + точные англ. запросы.
game   = сцена про конкретную игру/фичу/предмет/UI Roblox → реальный кадр Roblox (геймплей/интерфейс/предмет).
archive= реальные события/люди/новости/суды/аресты/расследования → новостной кадр или фото.
stock  = чисто атмосферное (код на экране, хакер за клавиатурой, деньги, тёмная комната) → сток.
Карточки (topic_card/level_card) не трогаем. Пишет media_plan_dw.json {sid:{bucket,query,fallback,film}}."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.llm.claude import ClaudeService

PROJECT = ROOT / "projects" / "2026-09-05_aysberg-robloks-temnaya-skrytaya-storona-realnye-intsidenty-"
CHUNK = 30
CARD_TYPES = {"topic_card", "level_card"}

SYSTEM = ("Ты — подборщик медиа для документального YouTube-айсберга про тёмную сторону Roblox. Главный "
          "визуал — реальные КАДРЫ Roblox (геймплей, интерфейс, предметы, аватары), реальные новостные "
          "кадры/фото событий (взломы, аресты, суды, расследования) и реальные лица (основатели, "
          "журналисты). Только реальное, без AI-арта.")

RULES = """Для КАЖДОЙ сцены выбери корзину и англ. запрос. Верни JSON-массив
{"id","bucket","query","fallback","film"}:

- bucket="game" — сцена про КОНКРЕТНУЮ игру/фичу/предмет/UI/аватар Roblox → нужен реальный КАДР Roblox.
  query = точный YouTube/поиск, напр. "Roblox DynaBlocks 2004 early gameplay", "Roblox Tix tickets currency old UI",
  "Roblox guest account gameplay 2010", "Roblox Dominus hat item", "Roblox limited items catalog", "Adopt Me
  trading pets gameplay", "Bloxflip roblox gambling site", "Roblox Rocket Arena Fizze oldest game", "Roblox avatar
  editor", "Roblox robux purchase screen". field "film" = что именно (игра/фича/предмет).
- bucket="archive" — реальные СОБЫТИЯ/люди/новости/суды/аресты/расследования: основатели (David Baszucki, Erik
  Cassel), взломы, утечки, аресты хакеров (Львов/Украина), иски штатов, расследования Vice/Forbes/Bloomberg,
  People Make Games. query = точный поиск реального НОВОСТНОГО кадра/ФОТО (напр. "David Baszucki Roblox CEO",
  "Ukraine police cybercrime arrest 2026", "Roblox lawsuit Texas Paxton news", "Vice Roblox beaming investigation",
  "hacker arrested computers seized police").
- bucket="stock" — только если сцена чисто атмосферная и конкретного кадра нет (код на экране, хакер в капюшоне
  за клавиатурой, поток данных, стопки денег/крипта, тёмная комната, фишинг-сайт, замок/безопасность). query = сток-запрос.

ПРАВИЛО: если в сцене есть конкретная игра/предмет/событие/человек — НЕ лей абстрактный сток, дай реальный кадр (game/archive).
Запросы на английском, конкретные. Дай и query, и запасной fallback (шире/проще).
Верни ТОЛЬКО JSON-массив."""


def main() -> int:
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    outline = json.loads((PROJECT / "outline.json").read_text(encoding="utf-8"))
    id2title = {}
    for L in outline["levels"]:
        for t in L["topics"]:
            id2title[t["id"]] = t["title"]
    targets = [s for s in scenes if (s.get("visual") or {}).get("type") not in CARD_TYPES]
    print(f"сцен всего: {len(scenes)} | к классификации: {len(targets)}")

    llm = ClaudeService(model="google/gemini-2.5-flash")
    plan = {}
    for i in range(0, len(targets), CHUNK):
        chunk = targets[i:i + CHUNK]
        lines = []
        for s in chunk:
            topic = id2title.get(s.get("topic_id"), "")
            vo = (s.get("voiceover") or "").replace('"', " ")[:180]
            lines.append(f'{{"id":"{s["id"]}","topic":"{topic}","vo":"{vo}"}}')
        try:
            res = llm.call_json(RULES + "\n\nСЦЕНЫ:\n" + "\n".join(lines),
                                max_tokens=8000, temperature=0.2, system=SYSTEM)
            if isinstance(res, dict): res = res.get("items") or res.get("scenes") or []
            for r in res:
                if r.get("id"): plan[r["id"]] = r
        except Exception as e:
            print(f"  чанк {i//CHUNK+1} упал: {str(e)[:60]}")
        print(f"  {min(i+CHUNK,len(targets))}/{len(targets)}")

    (PROJECT / "media_plan_dw.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    import collections
    c = collections.Counter(v.get("bucket") for v in plan.values())
    print(f"\nИТОГ по корзинам: {dict(c)} | всего {len(plan)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
