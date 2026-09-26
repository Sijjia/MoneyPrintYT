"""Из пула тем Adult Swim строит ЧЕРНОВОЙ outline айсберга (4 уровня × ~5 тем, прогрессия
верхушка→бездна). Приоритет ПОДТВЕРЖДЁННЫМ фактам + интересное; попса и голая конспирология — вон.
Пишет adultswim_outline_draft.json + печатает."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.llm.claude import ClaudeService

S = Path(r"C:\Users\aidar\AppData\Local\Temp\claude\C--Users-aidar-OneDrive--------------automotization-youtube\0a3edf5b-8f55-4b33-a918-972784adb4ef\scratchpad")

SYSTEM = ("Ты — сценарист YouTube-канала «Айсберг» (RU). Собираешь outline айсберга про Adult Swim "
          "(ночной блок Cartoon Network). ГЛАВНОЕ: только реальные ПОДТВЕРЖДЁННЫЕ факты + реально "
          "интересное зрителю. Малоизвестное-но-железное > попсы-и-спорного. Спорное подавать как "
          "гипотезу. Никакой ИИшности. Прогрессия: верхушка (известное/лёгкое) → бездна (тёмное/жуткое/редкое).")

RULES = """Из пула тем собери outline айсберга: 4 УРОВНЯ по ~5 тем (всего ~20).
- Уровень 1 = верхушка (узнаваемое, лёгкий вход), Уровень 4 = бездна (самое тёмное/жуткое/редкое).
- Бери приоритетно kind=факт со strength 4-5. Отсеки чистую конспирологию и попсу-затычки.
- Внутри — микс: пара узнаваемых крючков + малоизвестное железное.
- Дай каждому уровню НАЗВАНИЕ (атмосферное, в стиле айсберга).
- Для каждой темы: {"id":"L.N","title":"кратко и цепляюще","fact":"1-2 фразы сути (что правда)","kind":"факт|гипотеза"}.

Верни ТОЛЬКО JSON: {"title":"рабочее название ролика","levels":[{"level":1,"name":"...","topics":[...]},...]}."""


def main() -> int:
    pool = json.loads((S / "adultswim_topic_pool.json").read_text(encoding="utf-8"))
    llm = ClaudeService(model="anthropic/claude-sonnet-4.5")
    res = llm.call_json(RULES + "\n\nПУЛ ТЕМ:\n" + json.dumps(pool, ensure_ascii=False)[:70000],
                        max_tokens=8000, temperature=0.4, system=SYSTEM)
    (S / "adultswim_outline_draft.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"РОЛИК: {res.get('title')}\n")
    for L in res.get("levels", []):
        print(f"━━ УРОВЕНЬ {L.get('level')}: {L.get('name')} ━━")
        for t in L.get("topics", []):
            print(f"  {t.get('id')} [{t.get('kind')}] {t.get('title')}")
            print(f"       {(t.get('fact') or '')[:90]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
