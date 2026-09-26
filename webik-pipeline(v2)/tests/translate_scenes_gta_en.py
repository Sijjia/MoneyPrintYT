"""Переводит voiceover всех сцен RU→EN (док-нарратив, US-аудитория) для GTA-айсберга (Debik).
Пишет EN scenes.json. Батчами через sonnet."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.llm.claude import ClaudeService

RU = ROOT / "projects" / "2026-09-06_aysberg-gta-temnaya-storona-realnye-dela-vnutriigrovye-tayny"
EN = ROOT / "projects" / "2026-09-06_aysberg-gta-temnaya-storona-realnye-dela-vnutriigrovye-tayny_EN"

SYSTEM = ("You are a professional documentary translator/localizer. Translate Russian YouTube "
          "documentary narration into natural, cinematic US English for a dark 'iceberg' documentary "
          "about Grand Theft Auto (GTA). Keep the ominous, factual, restrained tone. Same meaning, same "
          "length feel — not word-for-word, but natural spoken narration. Keep proper nouns in their "
          "official English form (GTA V, GTA VI, GTA San Andreas, Rockstar, Take-Two, NoPixel, Twitch, "
          "Bigfoot, Mount Chiliad, Fort Zancudo, Hot Coffee, Arion Kurtaj, Lapsus$, Devin Moore, xQc, "
          "Jack Thompson, etc.). Keep pause markers like [пауза 2с] as [pause] and level lines natural. "
          "No added commentary.")

RULES = """Translate each line's Russian narration to English. Return ONLY a JSON object mapping
scene id -> English narration string. Keep it natural spoken documentary English, same tone.
Lines (id ||| russian):"""


def main() -> int:
    scenes = json.loads((RU / "scenes.json").read_text(encoding="utf-8"))
    body = scenes["scenes"]
    todo = [(s["id"], s.get("voiceover") or "") for s in body if (s.get("voiceover") or "").strip()]
    print(f"сцен с текстом: {len(todo)}", flush=True)
    llm = ClaudeService(model="anthropic/claude-sonnet-4.5")
    out = {}
    B = 40
    for i in range(0, len(todo), B):
        batch = todo[i:i + B]
        lines = "\n".join(f'{sid} ||| {txt}' for sid, txt in batch)
        res = llm.call_json(RULES + "\n" + lines, max_tokens=8000, temperature=0.3, system=SYSTEM)
        if isinstance(res, list):
            res = {r.get("id"): (r.get("en") or r.get("text") or r.get("translation")) for r in res if r.get("id")}
        got = {k: v for k, v in (res or {}).items() if v}
        out.update(got)
        print(f"  батч {i//B+1}: {len(got)}/{len(batch)}", flush=True)
    miss = 0
    for s in body:
        sid = s["id"]
        if sid in out:
            s["voiceover"] = out[sid]
        elif (s.get("voiceover") or "").strip():
            miss += 1
    (EN / "scenes.json").write_text(json.dumps(scenes, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nпереведено {len(out)}/{len(todo)} | не переведено {miss} | → {EN/'scenes.json'}", flush=True)
    return 0 if miss <= 3 else 1


if __name__ == "__main__":
    sys.exit(main())
