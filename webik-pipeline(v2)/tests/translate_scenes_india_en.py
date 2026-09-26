"""Переводит voiceover всех сцен RU→EN (док-нарратив, US-аудитория) для «Айсберг Индии» (Debik).
Пишет EN scenes.json. Батчами через sonnet."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.llm.claude import ClaudeService

RU = ROOT / "projects" / "2026-09-22_aysberg-indii-misticheskaya-i-zagadochnaya-storona-strany"
EN = ROOT / "projects" / "2026-09-22_aysberg-indii-misticheskaya-i-zagadochnaya-storona-strany_EN"

SYSTEM = ("You are a professional documentary translator/localizer. Translate Russian YouTube "
          "documentary narration into natural, cinematic US English for a dark 'iceberg' documentary "
          "about the mystical, hidden and disturbing side of India. Keep the ominous, factual, restrained, "
          "respectful tone (religion/caste handled with respect, legends framed as legends). "
          "Same meaning, same length feel — not word-for-word, but natural spoken narration. "
          "Keep proper nouns in their official English form: Taj Mahal, Ustad Ahmad Lahauri, Shah Jahan, "
          "Mumtaz Mahal, Varanasi, the Ganges, the ghats, Kumbh Mela, sadhu, Aghori, Bhangarh Fort, "
          "Archaeological Survey of India (ASI), Kuldhara, Karni Mata (the rat temple), Deshnoke, "
          "Cherrapunji, living root bridges, Roopkund Lake (Skeleton Lake), Jatinga, Kodinhi (the village "
          "of twins), Kongka La, Ladakh, Magnetic Hill, Thugs / Thuggee, the cult of Kali, William Sleeman, "
          "Padmanabhaswamy Temple, Vault B, Patala, Naga (serpent beings), North Sentinel Island, the "
          "Sentinelese, John Allen Chau, Asaram Bapu, Gurmeet Ram Rahim Singh, Yama (god of death), Durga, "
          "Netaji Subhas Chandra Bose, Rajasthan, the Himalayas. "
          "Convert Russian number-words to natural English narration (e.g. 'двадцать две тысячи' -> "
          "'twenty-two thousand'). Keep pause markers like [пауза 2с] as [pause] and [long pause] as-is. "
          "Never leave Cyrillic or a bare '/' a TTS engine would misread. No added commentary.")

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
