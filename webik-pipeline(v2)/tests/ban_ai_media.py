"""Перевод ai_image/ai_video/diagram сцен в РЕАЛЬНОЕ тематическое медиа (правило Айдара:
никакого AI, только реальное фото/видео по теме). LLM (дешёвая модель) переразмечает
только эти сцены → тип archive/archive_video/stock_video/stock_photo + англ. search_query.
Остальные сцены не трогаем."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.llm.claude import ClaudeService

PROJECT = ROOT / "projects" / "2026-08-18_aysberg-evolyutsii-temnaya-i-zapretnaya-storona-evolyutsii-o"
BAN = {"ai_image", "ai_video", "diagram"}
CHUNK = 40

SYSTEM = (
    "Ты — подборщик РЕАЛЬНОГО документального медиа для YouTube-айсберга про эволюцию. "
    "Никакого AI-арта. Только то, что реально существует и находится в стоках/архивах."
)

RULES = """Переразметь КАЖДУЮ сцену на РЕАЛЬНЫЙ тип медиа. Разрешённые типы:
- "archive"        — реальное СТАТИЧНОЕ фото (исторические снимки, окаменелости, ФОТО музейных
                     реконструкций вымерших видов, портреты учёных, документы, места)
- "archive_video"  — реальные АРХИВНЫЕ видеокадры (историческая хроника: евгеника, нацизм, лаборатории прошлого)
- "stock_video"    — реальное СТОК-видео (макросъёмка паразитов/грибов/насекомых, ДНК/клетки/микроскоп,
                     природа, животные, современные лаборатории, толпы, руки)
- "stock_photo"    — реальное сток-фото (когда нужно статичное современное изображение)

ЗАПРЕЩЕНО: ai_image, ai_video, diagram, level_card, topic_card.

Как выбирать:
- Вымершие люди (денисовцы, хоббит Флореса, неандерталец) → "archive", query про МУЗЕЙНУЮ РЕКОНСТРУКЦИЮ/бюст/окаменелость,
  напр. "Homo floresiensis reconstruction museum model", "Neanderthal skull fossil", "Denisovan reconstruction model".
- Паразиты/грибы/насекомые (кордицепс, оса-изумрудка, волосатик, улитка) → "stock_video" реальное макро,
  напр. "Ophiocordyceps zombie ant fungus macro", "jewel wasp cockroach parasite", "snail Leucochloridium".
- Генетика/концепции (ДНК, геном, бутылочное горлышко, вирусы, синцитин, CRISPR, химеры) → "stock_video",
  напр. "DNA double helix animation microscope", "human embryo cells laboratory", "virus particles microscope".
- История (евгеника США, T-4/Лебенсборн, Швеция, лисы Беляева) → "archive" или "archive_video" реальная хроника/фото.
- Животные/охота/эволюция (слоны, бараны, лисы) → "stock_video" реальная съёмка животных.

Запросы — на АНГЛИЙСКОМ, конкретные, находимые в реальных стоках/архивах. Дай и search_query, и запасной fallback_query (проще/шире).

Верни СТРОГО JSON-массив объектов: {"id": "...", "type": "...", "search_query": "...", "fallback_query": "..."} для каждой переданной сцены."""


def main() -> int:
    data = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))
    scenes = data["scenes"]
    targets = [s for s in scenes if (s.get("visual") or {}).get("type") in BAN]
    print(f"всего сцен: {len(scenes)} | к переразметке (ai/diagram): {len(targets)}")
    if not targets:
        print("нечего менять"); return 0

    llm = ClaudeService(model="google/gemini-2.5-flash")
    remap = {}
    for i in range(0, len(targets), CHUNK):
        chunk = targets[i:i + CHUNK]
        lines = []
        for s in chunk:
            vo = (s.get("voiceover") or "").replace("\n", " ").strip()
            ai = ((s.get("visual") or {}).get("ai_prompt") or "").replace("\n", " ")[:120]
            lines.append(f'{{"id":"{s["id"]}","было":"{(s.get("visual") or {}).get("type")}",'
                         f'"закадр":"{vo[:180]}","идея":"{ai}"}}')
        prompt = RULES + "\n\nСЦЕНЫ:\n" + "\n".join(lines)
        print(f"  чанк {i//CHUNK+1}: {len(chunk)} сцен → LLM...")
        res = llm.call_json(prompt, max_tokens=8000, temperature=0.4, system=SYSTEM)
        if isinstance(res, dict):
            res = res.get("items") or res.get("scenes") or []
        for r in res:
            if r.get("id") and r.get("type") in {"archive", "archive_video", "stock_video", "stock_photo"}:
                remap[r["id"]] = r

    applied = 0
    for s in scenes:
        r = remap.get(s["id"])
        if not r:
            continue
        v = s.setdefault("visual", {})
        v["type"] = r["type"]
        v["search_query"] = r.get("search_query") or v.get("search_query") or ""
        v["fallback_query"] = r.get("fallback_query") or v.get("fallback_query") or ""
        v.pop("ai_prompt", None)
        applied += 1

    (PROJECT / "scenes.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    from collections import Counter
    dist = Counter((s.get("visual") or {}).get("type") for s in scenes)
    print(f"\nпереразмечено: {applied}/{len(targets)}")
    print("новое распределение:")
    for k, c in dist.most_common():
        print(f"  {k}: {c} ({c/len(scenes)*100:.1f}%)")
    left = sum(dist[t] for t in BAN if t in dist)
    print(f"осталось ai/diagram: {left}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
