"""Классифицирует сцены «Айсберг GTA» на корзины медиа + точные англ. запросы.
game   = сцена про конкретную игру/миссию/пасхалку/локацию GTA → реальный КАДР геймплея.
archive= реальные события/люди/новости/суды/аресты/стримы/RP → новостной кадр, фото, клип стрима.
stock  = чисто атмосферное (хакер, код на экране, зал суда, деньги, тёмная комната) → сток.
Карточки не трогаем. Пишет media_plan_dw.json {sid:{bucket,query,fallback,film}}."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.llm.claude import ClaudeService

PROJECT = ROOT / "projects" / "2026-09-06_aysberg-gta-temnaya-storona-realnye-dela-vnutriigrovye-tayny"
CHUNK = 30
CARD_TYPES = {"topic_card", "level_card"}

SYSTEM = ("Ты — подборщик медиа для документального YouTube-айсберга про тёмную сторону GTA (Grand Theft "
          "Auto). Главный визуал — реальные КАДРЫ геймплея нужной игры серии (San Andreas, IV, V, GTA "
          "Online, трейлер VI), реальные новостные/судебные кадры и фото событий (утечка, аресты, иски), "
          "клипы GTA RP / стримеров (NoPixel, xQc). Только реальное, без AI-арта.")

RULES = """Для КАЖДОЙ сцены выбери корзину и англ. запрос. Верни JSON-массив
{"id","bucket","query","fallback","film"}:

- bucket="game" — сцена про КОНКРЕТНУЮ игру/миссию/пасхалку/локацию/предмет GTA → реальный КАДР геймплея.
  query = точный YouTube/поиск, напр. "GTA San Andreas Bigfoot myth forest gameplay", "GTA V Mount Chiliad
  mystery mural", "GTA V Jolene ghost Mount Gordo easter egg", "GTA V UFO 100% completion", "GTA V The Last
  One Bigfoot mission", "GTA V Epsilon program cult mission", "GTA V torture scene By the Book", "GTA V
  Infinity Killer bodies", "GTA San Andreas Hot Coffee mod", "GTA VI trailer 1", "GTA V jetpack Thruster".
  field "film" = какая игра/что именно.
- bucket="archive" — реальные СОБЫТИЯ/люди/новости/суды/стримы: утечка GTA VI 2022, хакер Arion Kurtaj/суд,
  Джек Томпсон, иски Hot Coffee, NoPixel/xQc стримы, копи-кат дела. query = точный поиск реального
  НОВОСТНОГО кадра/ФОТО/клипа стрима (напр. "GTA 6 leak 2022 news", "Arion Kurtaj hacker court news",
  "Jack Thompson lawyer GTA lawsuit", "xQc NoPixel GTA RP stream", "Hot Coffee GTA ESRB news 2005").
- bucket="stock" — только если сцена чисто атмосферная и конкретного кадра нет (хакер в капюшоне за
  клавиатурой, код на экране, зал суда, стопки денег, тёмная комната, серверные стойки). query = сток-запрос.

ПРАВИЛО: если в сцене есть конкретная игра/миссия/пасхалка/событие/человек — НЕ лей абстрактный сток,
дай реальный кадр (game/archive). Запросы на английском, конкретные. Дай и query, и запасной fallback.
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
