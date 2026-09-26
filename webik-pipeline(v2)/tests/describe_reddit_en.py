"""EN-описание для «Iceberg Reddit» (Debik). Таймкоды и тексты плашек — ДИНАМИЧЕСКИ с EN-таймлайна
(level_card / topic_card из scenes.json + alignment.json). Пишет meta_EN.md в E:\\...\\Deb1k\\Iceberg Reddit."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EN = ROOT / "projects" / "2026-09-13_aysberg-reddit-strannaya-i-trevozhnaya-storona_EN"
OUT = Path(r"E:\video for ytb\Deb1k\Iceberg Reddit")

TITLE = "The REDDIT ICEBERG — Creepypastas, Ciphers, Moral Panics & the Darkest Corners of Reddit"
HOOK = ("Reddit is more than memes and discussions. Beneath the surface lies a labyrinth of strange "
        "experiments, unsolved mysteries and stories that blur the line between fiction and reality. "
        "From the nosleep legends and the Backrooms to the Cicada 3301 cipher hunt, the Boston Marathon "
        "witch-hunt that named innocent people, the Blue Whale and Momo panics manufactured out of thin "
        "air, and mysteries no one has ever cracked — this is the full Reddit iceberg, from the surface "
        "legends down to the coldest, darkest depths.")

TAGS = ["reddit iceberg", "reddit dark side", "creepypasta", "nosleep", "cicada 3301", "the backrooms",
        "mandela effect", "this man", "blue whale challenge", "momo", "lake city quiet pills",
        "swamps of dagobah", "11b-x-1371", "internet mysteries", "arg", "boston marathon reddit",
        "reddit documentary", "iceberg explained", "internet iceberg", "unsolved mysteries"]


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

    parts = [TITLE, "", HOOK, "", "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", "TIMECODES:"]
    parts += lines
    parts += ["", "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
              "👉 Subscribe for more deep-dive internet icebergs.", "",
              "TAGS: " + ", ".join(TAGS)]
    txt = "\n".join(parts)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "meta_EN.md").write_text(txt, encoding="utf-8")
    topics = sum(1 for r in rows if r[2] == "topic")
    print(f"meta_EN.md → {OUT}")
    print(f"TITLE: {TITLE}")
    print(f"topics: {topics} | levels: {sum(1 for r in rows if r[2]=='level')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
