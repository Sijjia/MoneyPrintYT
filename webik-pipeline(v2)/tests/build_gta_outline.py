"""Собирает полный outline.json из УТВЕРЖДЁННОГО драфта Roblox (20 тем, 4×5).
Сохраняет РОВНО наши темы, расширяет key_points реальными деталями из note + интро/переходы/сео.
Мифы подаём КАК мифы (+разоблачение), чувствительное — мягко по новостям. Только факты."""
import glob, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.llm.claude import ClaudeService

S = Path(r"C:\Users\aidar\AppData\Local\Temp\claude\C--Users-aidar-OneDrive--------------automotization-youtube\0a3edf5b-8f55-4b33-a918-972784adb4ef\scratchpad")
PROJ = Path(sorted(glob.glob(str(ROOT / "projects" / "2026-09-06_aysberg-gta*")))[0])
LEVELS = {1: "ВЕРХУШКА АЙСБЕРГА", 2: "ВОДНАЯ ГЛАДЬ", 3: "ПОГРУЖЕНИЕ", 4: "БЕЗДНА"}

SYSTEM = ("Ты — сценарист-редактор YouTube-канала «Айсберг» (RU). Собираешь outline.json ролика про "
          "тёмную/скрытую сторону Roblox. ЖЕЛЕЗНОЕ правило: только РЕАЛЬНЫЕ, подтверждённые факты (в "
          "драфте у каждой темы есть note с деталями и источниковой сутью — опирайся на него). Темы со "
          "status=myth подавай КАК миф/легенду и ОБЯЗАТЕЛЬНО разоблачай (что выдумано, что правда на "
          "деле). Темы sensitive (хищники/несовершеннолетние/condo) — строго по новостям, БЕЗ сенсации, "
          "БЕЗ имён и деталей, спокойно и по фактам. Стиль тёмно-документальный, чистый, без ИИшности, "
          "без дешёвых вставок и без мягких выводов-осмыслений.")

RULES = """Ниже УТВЕРЖДЁННЫЕ 20 тем (4 уровня × 5) с пометками status (real/myth) и note (реальная суть).
Собери полный outline.json РОВНО по этим темам (НЕ меняй, НЕ добавляй, НЕ убирай; порядок внутри
уровня можешь улучшить для нарратива).

Схема (соблюдай ключи):
{
 "title": "цепляющее название ролика (с «Айсберг GTA»)",
 "preset": "auto",
 "estimated_duration_min": 25,
 "intro_hook": "короткий мощный хук БЕЗ перечисления тем (1-2 фразы)",
 "intro_text": "вступление 3-5 фраз, задаёт тон",
 "levels": [{"level":1,"title":"УРОВЕНЬ 1: ВЕРХУШКА АЙСБЕРГА","topics":[
     {"id":"1.1","title":"... РОВНО как в драфте","duration_sec":110,
      "key_points":["4-6 КОНКРЕТНЫХ реальных пунктов из note: что, когда, кто, цифры/детали; для myth-тем — что миф выдумал и что правда"]}
 ]}, ... 4 уровня],
 "transitions_between_levels": ["фраза-переход на 2 уровень","...на 3","...на 4"],
 "outro_text": "заключение, чистый обрыв без ложных концовок и без пустых философствований",
 "cta_text": "короткий призыв",
 "thumbnail_concept": "идея превью (айсберг + узнаваемый объект GTA)",
 "youtube_seo": {"description":"...","tags":["..."]}
}
Названия уровней РОВНО: 1=ВЕРХУШКА АЙСБЕРГА, 2=ВОДНАЯ ГЛАДЬ, 3=ПОГРУЖЕНИЕ, 4=БЕЗДНА.
duration_sec на тему ~90-140. key_points — РЕАЛЬНЫЕ детали из note (НЕ выдумывай новых фактов/дат/цифр).
Верни ТОЛЬКО JSON."""


def main() -> int:
    draft = json.loads((S / "gta_outline_draft.json").read_text(encoding="utf-8"))
    topics_txt = json.dumps(draft, ensure_ascii=False, indent=1)
    llm = ClaudeService(model="anthropic/claude-sonnet-4.5")
    out = llm.call_json(RULES + "\n\nУТВЕРЖДЁННЫЕ ТЕМЫ:\n" + topics_txt,
                        max_tokens=14000, temperature=0.5, system=SYSTEM)
    for L in out.get("levels", []):
        L["title"] = f"УРОВЕНЬ {L['level']}: {LEVELS.get(L['level'], '')}"
    ntop = sum(len(L.get("topics", [])) for L in out.get("levels", []))
    (PROJ / "outline.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"outline.json → {PROJ.name}")
    print(f"title: {out.get('title')}")
    print(f"тем: {ntop} (должно 20) | уровней: {len(out.get('levels', []))}")
    print(f"hook: {out.get('intro_hook')}")
    for L in out.get("levels", []):
        print(f"  {L['title']}: {', '.join(t['title'][:26] for t in L['topics'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
