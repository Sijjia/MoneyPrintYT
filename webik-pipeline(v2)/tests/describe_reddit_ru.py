"""RU-описание для «Айсберг Reddit» (Webik). Таймкоды и тексты плашек — ДИНАМИЧЕСКИ с RU-таймлайна
(level_card / topic_card из scenes.json + alignment.json). Пишет meta_RU.md в E:\\...\\Webik\\Айсберг Reddit.
ФУТЕР ссылок/концовки — свой для канала, см. память reference_description_links (RU≠EN)."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EN = ROOT / "projects" / "2026-09-13_aysberg-reddit-strannaya-i-trevozhnaya-storona"
OUT = Path(r"E:\video for ytb\Webik\Айсберг Reddit")

TITLE = "АЙСБЕРГ REDDIT — крипипасты, шифры, моральные паники и самые тёмные углы Reddit"
HOOK = ("Reddit — это не только мемы и обсуждения. Под поверхностью прячется лабиринт странных "
        "экспериментов, нераскрытых тайн и историй, стирающих грань между вымыслом и реальностью. "
        "От легенд nosleep и Backrooms до охоты за шифром Cicada 3301, бостонской охоты на ведьм, "
        "заклеймившей невиновных, паник Blue Whale и Момо, сфабрикованных из воздуха, и загадок, которые "
        "никто так и не разгадал — это полный айсберг Reddit, от поверхностных легенд до самого тёмного дна.")

TAGS = ["айсберг reddit", "reddit", "крипипаста", "nosleep", "cicada 3301", "backrooms", "эффект манделы",
        "this man", "синий кит", "момо", "lake city quiet pills", "swamps of dagobah", "11b-x-1371",
        "тайны интернета", "arg", "страшные истории reddit", "айсберг", "тёмная сторона reddit",
        "разбор айсберга", "нераскрытые тайны"]

# Футер канала Webik (RU) — постоянный, см. память reference_description_links. EN(Debik) футера пока НЕТ.
FOOTER_RU = ("НАШ ТЕЛЕГРАМ-КАНАЛ – https://t.me/webik_studio\n\n"
             "Поддержка канала - https://www.donationalerts.com/r/webikstudio\n\n"
             "По сотрудничеству пишите - aidarbekr2@gmail.com")


def tc(s):
    return f"{int(s // 60):02d}:{int(s % 60):02d}"


def main() -> int:
    sc = json.loads((EN / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    al = json.loads((EN / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    rows = [(0.0, "Intro", "intro")]
    for s in sc:
        vt = (s.get("visual") or {}).get("type")
        if vt not in ("level_card", "topic_card"):
            continue
        st = al.get(s["id"], {}).get("start", 0)
        txt = (s.get("voiceover") or (s.get("visual") or {}).get("text") or "").strip().rstrip(".")
        rows.append((st, txt, "level" if vt == "level_card" else "topic"))
    rows.sort(key=lambda r: (r[0], {"intro": 0, "level": 1, "topic": 2}[r[2]]))

    lines = []
    for st, t, k in rows:
        if k == "level":
            lines.append("")
            lines.append(f"{tc(st)} ▬ {t}")
        else:
            lines.append(f"{tc(st)} {t}")

    parts = [TITLE, "", HOOK, "", "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", "ТАЙМКОДЫ:"]
    parts += lines
    parts += ["", "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
              "👉 Подписывайся — впереди новые айсберги тёмного интернета.", "",
              FOOTER_RU, "",
              "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
              "TAGS: " + ", ".join(TAGS)]
    txt = "\n".join(parts)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "meta_RU.md").write_text(txt, encoding="utf-8")
    topics = sum(1 for r in rows if r[2] == "topic")
    print(f"meta_RU.md → {OUT}")
    print(f"TITLE: {TITLE}")
    print(f"topics: {topics} | levels: {sum(1 for r in rows if r[2]=='level')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
