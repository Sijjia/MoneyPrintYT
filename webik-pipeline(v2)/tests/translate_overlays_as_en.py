"""Переводит текстовые поля EN overlays.json RU→EN (детектор выдаёт русский).
Числа/suffix/year не трогает. Имена собственные — в офиц. англ. форму."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.llm.claude import ClaudeService

EN = ROOT / "projects" / "2026-08-31_aysberg-adult-swim-temnaya-skrytaya-storona-nochnogo-bloka-c_EN"

SYSTEM = ("You localize on-screen graphic labels for an English documentary about Adult Swim. "
          "Translate Russian UI/graphic text to concise natural US English. Proper nouns → official "
          "English form (Sam Hyde, Brett Gelman, Naruto, Delilah, Space Ghost Coast to Coast, Mooninite, "
          "Boston, Berdovsky, Stevens...). Keep it SHORT (fits on screen), UPPERCASE stays uppercase. "
          "Return ONLY a JSON object mapping key -> English string.")


def collect(ov):
    """→ {key: ru_text}, key = 'idx.field' или 'idx.events.j.label'"""
    m = {}
    for i, o in enumerate(ov):
        p = o.get("props", {})
        for f in ("label", "name", "sub", "phrase", "title", "text", "author"):
            v = p.get(f)
            if isinstance(v, str) and v.strip():
                m[f"{i}.{f}"] = v
        for j, ev in enumerate(p.get("events", []) or []):
            if isinstance(ev.get("label"), str) and ev["label"].strip():
                m[f"{i}.events.{j}.label"] = ev["label"]
        for j, it in enumerate(p.get("items", []) or []):
            if isinstance(it.get("label"), str) and it["label"].strip():
                m[f"{i}.items.{j}.label"] = it["label"]
    return m


def apply(ov, tr):
    for key, en in tr.items():
        parts = key.split(".")
        i = int(parts[0]); p = ov[i]["props"]
        if len(parts) == 2:
            p[parts[1]] = en
        elif parts[1] in ("events", "items"):
            p[parts[1]][int(parts[2])][parts[3]] = en


def main() -> int:
    data = json.loads((EN / "overlays.json").read_text(encoding="utf-8"))
    ov = data["overlays"]
    m = collect(ov)
    print(f"строк к переводу: {len(m)}")
    llm = ClaudeService(model="anthropic/claude-sonnet-4.5")
    tr = {}
    keys = list(m.keys())
    B = 60
    for i in range(0, len(keys), B):
        chunk = {k: m[k] for k in keys[i:i + B]}
        prompt = "Translate these (key ||| russian):\n" + "\n".join(f"{k} ||| {v}" for k, v in chunk.items())
        res = llm.call_json(prompt, max_tokens=4000, temperature=0.2, system=SYSTEM)
        if isinstance(res, dict):
            tr.update({k: v for k, v in res.items() if isinstance(v, str) and v.strip()})
        print(f"  батч {i//B+1}: {len(tr)}/{len(m)}")
    apply(ov, tr)
    (EN / "overlays.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    # проверка на оставшуюся кириллицу
    left = sum(1 for v in collect(ov).values() if any('а' <= c.lower() <= 'я' for c in v))
    print(f"переведено {len(tr)}/{len(m)} | осталось с кириллицей: {left}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
