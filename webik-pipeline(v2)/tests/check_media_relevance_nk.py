"""LLM-проверка уместности медиа: для каждой сцены сверяем закадр (vo) против того,
что показывает медиа (поисковый запрос). Выдаём список сцен, где медиа НЕ по смыслу,
с причиной и лучшим запросом → _relevance_suspects.json."""
import io, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from services.llm.claude import ClaudeService
from core.config import get_settings

PROJ = ROOT / "projects" / "2026-08-08_aysberg-severnoy-korei-samye-zakrytye-zhutkie-i-maloizvestny"
CARD = {"level_card", "topic_card"}
BATCH = 25


def tc(s):
    s = int(round(s)); return f"{s//60:02d}:{s%60:02d}"


def main():
    scenes = json.loads((PROJ / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    manifest = json.loads((PROJ / "assets" / "images" / "manifest.json").read_text(encoding="utf-8"))
    al = json.loads((PROJ / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]

    items = []
    for s in scenes:
        sid = s["id"]; v = s.get("visual", {})
        if v.get("type") in CARD:
            continue
        man = manifest.get(sid, {})
        q = man.get("query") or v.get("search_query") or v.get("fallback_query") or ""
        items.append({"id": sid, "vo": (s.get("voiceover") or "").strip(), "media": q})

    svc = ClaudeService(model=get_settings().llm_model_cheap or None)
    suspects = []
    for i in range(0, len(items), BATCH):
        batch = items[i:i + BATCH]
        prompt = (
            "Ты — редактор документального ролика про Северную Корею. Для каждой сцены дан "
            "закадровый текст (vo) и ОПИСАНИЕ ТОГО, ЧТО ПОКАЗЫВАЕТ медиа на экране (media — "
            "англоязычный поисковый запрос, по которому подобрали видео/фото). Найди сцены, где "
            "медиа НЕ соответствует смыслу закадра: показывает совсем не то, вводит в заблуждение, "
            "не по теме или про другую страну/эпоху. НЕ придирайся к атмосферным/иллюстративным "
            "кадрам, которые в целом по теме. Верни СТРОГО JSON без пояснений: "
            '{\"mismatches\":[{\"id\":\"scene_XXX\",\"reason\":\"кратко почему не то\",'
            '\"better_query\":\"лучший англоязычный запрос под этот закадр\"}]}. '
            "Если все ок — пустой список.\n\nСЦЕНЫ:\n" +
            json.dumps(batch, ensure_ascii=False)
        )
        try:
            res = svc.call_json(prompt, max_tokens=4000, temperature=0.3)
            ms = res.get("mismatches", []) if isinstance(res, dict) else []
            suspects.extend(ms)
            print(f"  батч {i//BATCH+1}: сцен {len(batch)}, несоответствий {len(ms)}")
        except Exception as e:
            print(f"  батч {i//BATCH+1}: ошибка {str(e)[:80]}")

    # обогащаем таймкодом + закадром
    by = {s["id"]: s for s in items}
    enriched = []
    for m in suspects:
        sid = m.get("id")
        if sid not in by:
            continue
        st = al.get(sid, {}).get("start", 0)
        enriched.append({
            "id": sid, "tc": tc(st), "start": st,
            "vo": by[sid]["vo"][:90], "current": by[sid]["media"],
            "reason": m.get("reason", ""), "better_query": m.get("better_query", ""),
        })
    enriched.sort(key=lambda x: x["start"])
    (PROJ / "_relevance_suspects.json").write_text(
        json.dumps(enriched, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nВСЕГО подозрительных сцен: {len(enriched)} → _relevance_suspects.json")
    for e in enriched[:60]:
        print(f"  {e['tc']} {e['id']}: [{e['current'][:32]}] — {e['reason'][:55]}")


if __name__ == "__main__":
    main()
