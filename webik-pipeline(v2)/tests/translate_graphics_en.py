"""Переводит текст-поля graphics_plan_v2_dw.json RU→EN для Debik-графики (заголовки/штампы/лейблы/цитаты).
treatment и числа не трогаем. Пишет EN graphics_plan_v2_dw.json в EN-папке."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.llm.claude import ClaudeService

RU = ROOT / "projects" / "2026-08-25_aysberg-dreamworks-lost-media-i-temnaya-skrytaya-storona-stu"
EN = ROOT / "projects" / "2026-08-25_aysberg-dreamworks-lost-media-i-temnaya-skrytaya-storona-stu_EN"

SYSTEM = ("You localize on-screen motion-graphics text for a dark DreamWorks documentary (US English). "
          "Translate Russian labels/titles/stamps/quotes to concise, punchy English suitable for overlays. "
          "Keep film titles in official English. Stamps stay SHORT and uppercase (e.g. ОТМЕНЁН→CANCELLED, "
          "УНИЧТОЖЕН→DESTROYED, ВЫРЕЗАНО→CUT, ОСТАНОВЛЕНО→SHUT DOWN, ПОТЕРЯН→LOST). Keep it tight.")

RULES = """Translate every Russian string value in this graphics plan JSON to English.
Rules: keep the SAME JSON structure and keys; do NOT translate the "treatment" field or numeric values;
keep film titles official English; stamps/labels short & UPPERCASE; quotes natural.
Return ONLY the translated JSON object (same shape)."""


def main() -> int:
    plan = json.loads((RU / "graphics_plan_v2_dw.json").read_text(encoding="utf-8"))
    llm = ClaudeService(model="anthropic/claude-sonnet-4.5")
    # переводим по частям (по 10 сцен), чтобы не переполнить
    ids = list(plan.keys()); out = {}
    for i in range(0, len(ids), 10):
        chunk = {k: plan[k] for k in ids[i:i + 10]}
        res = llm.call_json(RULES + "\n\nJSON:\n" + json.dumps(chunk, ensure_ascii=False),
                            max_tokens=6000, temperature=0.2, system=SYSTEM)
        if isinstance(res, dict):
            out.update(res)
        print(f"  батч {i//10+1}: {len(res) if isinstance(res,dict) else 0} сцен", flush=True)
    # подстрахуемся: treatment из оригинала
    for k in out:
        if k in plan: out[k]["treatment"] = plan[k].get("treatment")
    (EN / "graphics_plan_v2_dw.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nпереведено график: {len(out)}/{len(plan)} → EN/graphics_plan_v2_dw.json")
    return 0 if len(out) == len(plan) else 1


if __name__ == "__main__":
    sys.exit(main())
