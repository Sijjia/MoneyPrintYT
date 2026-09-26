"""Классифицирует сцены «Айсберг DreamWorks» на корзины медиа + точные запросы.
movie  = кадр/сцена из конкретного мультфильма DreamWorks → yt-dlp (query '<Film> <moment> scene')
archive= реальные люди/студия/новости (Катценберг, Фарли, Спилберг, здание, увольнения) → фото
stock  = атмосферное/абстрактное → сток (только если ничего конкретного нет)
Карточки (topic_card/level_card) не трогаем.
Пишет media_plan_dw.json {sid: {bucket, query, fallback, film}}."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.llm.claude import ClaudeService

PROJECT = ROOT / "projects" / "2026-08-31_aysberg-adult-swim-temnaya-skrytaya-storona-nochnogo-bloka-c"
CHUNK = 30
CARD_TYPES = {"topic_card", "level_card"}

SYSTEM = ("Ты — подборщик медиа для документального YouTube-айсберга про Adult Swim (ночной блок "
          "Cartoon Network). Главный визуал — реальные КАДРЫ из обсуждаемых шоу/бамперов/скетчей и реальные "
          "новостные кадры/фото событий. Только реальное, без AI-арта.")

RULES = """Для КАЖДОЙ сцены выбери корзину и англ. запрос. Верни JSON-массив
{"id","bucket","query","fallback","film"}:

- bucket="movie" — сцена обсуждает конкретное ШОУ/скетч/бампер/эпизод Adult Swim → нужен реальный КАДР оттуда.
  query = точный YouTube-поиск, напр. "Too Many Cooks Adult Swim", "Unedited Footage of a Bear Adult Swim",
  "Space Ghost Coast to Coast Bee Gees interview", "Aqua Teen Hunger Force scene", "Toonami TOM 2012 return",
  "Rick and Morty adult swim", "Superjail violence scene", "The Eric Andre Show prank", "Off the Air Adult Swim",
  "Adult Swim bumper dawn is your enemy", "Metalocalypse scene". field "film" = название шоу/скетча.
- bucket="archive" — реальные СОБЫТИЯ/люди/новости: бостонская паника 2007 (news footage, LED-устройства,
  саперы), пресс-конференция про причёски (Berdovsky Stevens), реальные фото создателей (Mike Lazzo и т.п.).
  query = точный поиск реального НОВОСТНОГО кадра/ФОТО (напр. "Boston 2007 Mooninite bomb scare news",
  "Berdovsky Stevens haircut press conference", "Aqua Teen Boston bomb scare LED sign").
- bucket="stock" — только если сцена чисто атмосферная и конкретного кадра нет
  (напр. ночное ТВ, CRT-помехи/статика, тёмная комната со свечением телевизора, VHS-плёнка). query = сток-запрос.

ПРАВИЛО: если в сцене есть конкретное шоу/бампер/событие — НЕ лей абстрактный сток, дай реальный кадр (bucket movie/archive).
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
    print(f"→ media_plan_dw.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
