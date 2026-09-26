"""Описания YouTube для «Айсберг DreamWorks» (RU=Webik + EN=Debik): хук + ссылки(RU) + таймкоды по
уровням/темам (с ЖИВЫХ таймлайнов) + теги. Пишет meta_RU.md / meta_EN.md в E:\\...\\Айсберг DreamWorks\\."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.llm.claude import ClaudeService

RU_PROJ = ROOT / "projects" / "2026-08-25_aysberg-dreamworks-lost-media-i-temnaya-skrytaya-storona-stu"
SCRATCH = Path(r"C:\Users\aidar\AppData\Local\Temp\claude\C--Users-aidar-OneDrive--------------automotization-youtube\0a3edf5b-8f55-4b33-a918-972784adb4ef\scratchpad")
OUT = Path(r"E:\video for ytb\Webik\Айсберг DreamWorks")
RU_CONCL, EN_CONCL = 1796, 1942  # с живого RU / EN alignment
LINKS_RU = ("https://t.me/webik_studio - НОВОСТИ\n"
            "https://www.donationalerts.com/r/webikstudio - Поддержать чтобы выходило больше видео)")


def tc(s): return f"{int(s // 60):02d}:{int(s % 60):02d}"


def main() -> int:
    d = json.loads((RU_PROJ / "scenes.json").read_text(encoding="utf-8"))
    ti = d["topics_index"]; lt = d.get("level_titles", {})
    ru_tc = json.loads((SCRATCH / "ru_v4_tc.json").read_text())
    en_tc = json.loads((SCRATCH / "en_v4_tc.json").read_text())
    ru_tc = sorted(ru_tc); en_tc = sorted(en_tc)

    llm = ClaudeService(model="anthropic/claude-sonnet-4.5")
    payload = {"topics": [{"id": t["id"], "title": t["title"]} for t in ti],
               "levels": {k: v for k, v in lt.items()}}
    sysmsg = ("You write YouTube metadata for a dark 'iceberg' documentary channel about DreamWorks. "
              "RU channel Webik, EN channel Debik (US audience). Ominous, factual, punchy.")
    ask = ("From this topics+levels JSON, return ONLY JSON: {"
           "\"ru_title\": catchy RU video title (<95 chars, with АЙСБЕРГ), "
           "\"en_title\": catchy EN video title (<95 chars, with ICEBERG), "
           "\"ru_hook\": 2-3 sentence RU description opener (dark, intriguing), "
           "\"en_hook\": 2-3 sentence EN description opener, "
           "\"topics_en\": {id: English title}, \"levels_en\": {n: English level title}, "
           "\"tags\": [~15 mixed RU+EN youtube tags]}. Keep film titles official English.\n\n"
           + json.dumps(payload, ensure_ascii=False))
    r = llm.call_json(ask, max_tokens=4000, temperature=0.4, system=sysmsg)
    te = r.get("topics_en", {}); le = r.get("levels_en", {})

    def build(lang):
        tcs = ru_tc if lang == "ru" else en_tc
        concl = RU_CONCL if lang == "ru" else EN_CONCL
        intro = "Вступление" if lang == "ru" else "Intro"
        lvlword = "УРОВЕНЬ" if lang == "ru" else "LEVEL"
        conclword = "Заключение" if lang == "ru" else "Conclusion"
        lines = [f"00:00 {intro}"]
        cur_lvl = None
        for i, t in enumerate(ti):
            lvl = t["id"].split(".")[0]
            if lvl != cur_lvl:
                cur_lvl = lvl
                title = (lt.get(lvl, "") if lang == "ru" else le.get(lvl, le.get(str(lvl), lt.get(lvl, ""))))
                lines.append(f"\n{lvlword} {lvl}: {title.upper()}")
            ttl = t["title"] if lang == "ru" else te.get(t["id"], t["title"])
            lines.append(f"{tc(tcs[i])} {ttl}")
        lines.append(f"\n{tc(concl)} {conclword}")
        hook = r.get("ru_hook") if lang == "ru" else r.get("en_hook")
        title = r.get("ru_title") if lang == "ru" else r.get("en_title")
        parts = [f"# {title}\n", hook, ""]
        if lang == "ru":
            parts += [LINKS_RU, ""]
        parts += [("ТАЙМКОДЫ:" if lang == "ru" else "TIMECODES:")] + lines
        parts += ["", ("ТЕГИ: " if lang == "ru" else "TAGS: ") + ", ".join(r.get("tags", []))]
        return "\n".join(parts)

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "meta_RU.md").write_text(build("ru"), encoding="utf-8")
    (OUT / "meta_EN.md").write_text(build("en"), encoding="utf-8")
    print(f"meta_RU.md / meta_EN.md → {OUT}")
    print(f"RU title: {r.get('ru_title')}")
    print(f"EN title: {r.get('en_title')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
