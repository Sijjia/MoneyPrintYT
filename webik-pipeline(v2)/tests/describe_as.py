"""Описания YouTube для «Айсберг Adult Swim» (RU=Webik + EN=Debik): хук + ссылки(RU) + таймкоды
по уровням/темам (из карточек тем/уровней проекта) + теги. Пишет meta_RU.md / meta_EN.md в E:\\...."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.llm.claude import ClaudeService

RU = ROOT / "projects" / "2026-08-31_aysberg-adult-swim-temnaya-skrytaya-storona-nochnogo-bloka-c"
EN = ROOT / "projects" / "2026-08-31_aysberg-adult-swim-temnaya-skrytaya-storona-nochnogo-bloka-c_EN"
OUT = Path(r"E:\video for ytb\Webik\Айсберг Adult Swim")
LINKS_RU = ("https://t.me/webik_studio - НОВОСТИ\n"
            "https://www.donationalerts.com/r/webikstudio - Поддержать чтобы выходило больше видео)")
OUTRO_SECTIONS = {"outro", "cta", "conclusion"}


def tc(s): return f"{int(s // 60):02d}:{int(s % 60):02d}"


def build_timecodes(proj: Path, lang: str):
    scenes = json.loads((proj / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    al = json.loads((proj / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    intro = "Вступление" if lang == "ru" else "Intro"
    conclword = "Заключение" if lang == "ru" else "Conclusion"
    rows = []
    for s in scenes:
        vt = (s.get("visual") or {}).get("type")
        if vt in ("topic_card", "level_card"):
            st = al.get(s["id"], {}).get("start", 0)
            title = (s.get("voiceover") or "").strip().rstrip(".").strip()
            rows.append((st, vt, int(s.get("level", 0)), title))
    rows.sort()
    # заключение = самый ранний outro/cta/conclusion
    concl = None
    for s in scenes:
        if (s.get("section") or "") in OUTRO_SECTIONS:
            concl = min(concl or 1e9, al.get(s["id"], {}).get("start", 0))
    lines = [f"00:00 {intro}"]
    for st, vt, lv, title in rows:
        if vt == "level_card":
            lines.append(f"\n{title.upper()}")   # voiceover уже = «Уровень N: название»
        else:
            lines.append(f"{tc(st)} {title}")
    if concl:
        lines.append(f"\n{tc(concl)} {conclword}")
    return "\n".join(lines)


def main() -> int:
    ti = json.loads((RU / "scenes.json").read_text(encoding="utf-8"))["topics_index"]
    llm = ClaudeService(model="anthropic/claude-sonnet-4.5")
    payload = [{"id": t["id"], "title": t["title"]} for t in ti]
    sysmsg = ("You write YouTube metadata for a dark 'iceberg' documentary about Adult Swim (Cartoon "
              "Network's late-night block). RU channel Webik, EN channel Debik (US audience). Ominous, "
              "factual, punchy, NOT clickbait-cringe.")
    ask = ("From this topics list, return ONLY JSON: {"
           "\"ru_title\": catchy RU video title (<95 chars, contains АЙСБЕРГ Adult Swim), "
           "\"en_title\": catchy EN video title (<95 chars, contains ICEBERG Adult Swim), "
           "\"ru_hook\": 2-3 sentence RU description opener (dark, intriguing, real), "
           "\"en_hook\": 2-3 sentence EN description opener, "
           "\"tags\": [~15 mixed RU+EN youtube tags]}\n\n" + json.dumps(payload, ensure_ascii=False))
    r = llm.call_json(ask, max_tokens=3000, temperature=0.4, system=sysmsg)

    def compose(lang):
        title = r.get("ru_title") if lang == "ru" else r.get("en_title")
        hook = r.get("ru_hook") if lang == "ru" else r.get("en_hook")
        proj = RU if lang == "ru" else EN
        parts = [f"# {title}\n", hook, ""]
        if lang == "ru":
            parts += [LINKS_RU, ""]
        parts += [("ТАЙМКОДЫ:" if lang == "ru" else "TIMECODES:"), build_timecodes(proj, lang), ""]
        parts += [("ТЕГИ: " if lang == "ru" else "TAGS: ") + ", ".join(r.get("tags", []))]
        return "\n".join(parts)

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "meta_RU.md").write_text(compose("ru"), encoding="utf-8")
    (OUT / "meta_EN.md").write_text(compose("en"), encoding="utf-8")
    print(f"meta_RU.md / meta_EN.md → {OUT}")
    print(f"RU title: {r.get('ru_title')}")
    print(f"EN title: {r.get('en_title')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
