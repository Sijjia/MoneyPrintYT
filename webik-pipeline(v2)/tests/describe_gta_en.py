"""EN-описание для «Iceberg GTA» (Debik). Таймкоды сняты с ЖИВОГО EN-таймлайна (плашки тем V4 +
уровни), тексты плашек = voiceover announce-сцен (ровно что на экране и в озвучке).
Пишет meta_EN.md в E:\\video for ytb\\Deb1k\\Iceberg GTA\\."""
import json, sys
from pathlib import Path

OUT = Path(r"E:\video for ytb\Deb1k\Iceberg GTA")

# level cards (с живого таймлайна) + англ-названия уровней
LEVELS = [(26, 1, "LEGENDS. SECRETS."), (424, 2, "CULTS. CONSPIRACIES."),
          (824, 3, "EXPOSÉS. LEAKS."), (1224, 4, "HACKS. DARKNESS.")]
CONCL = 1739  # конец контента (V3), Conclusion-блок

# topic cards: (start_sec, on-screen title) — с живого таймлайна
TOPICS = [
    (30, "The GTA VI trailer record and GTA V's profitability"),
    (94, "Bigfoot in San Andreas — a legend hunted for years"),
    (168, "Mount Chiliad — the mysterious mural"),
    (253, "Hot Coffee — the hidden sex mini-game"),
    (342, "NoPixel 3.0 — how GTA RP exploded on Twitch (2021)"),
    (428, "The Ghost of Jolene Cranley-Evans at Mount Gordo"),
    (495, "UFOs at 100% and the sunken saucer"),
    (570, "The Epsilon Cult and Kifflom"),
    (651, "xQc: five NoPixel bans → secret server co-ownership"),
    (732, "Jack Thompson — the crusade against GTA"),
    (828, "Bigfoot resolution — 'The Last One' and Sasquatch"),
    (930, "Infinity Killer / Merle Abrahams"),
    (1007, "Rainbow Road — the greatest moments in GTA RP"),
    (1060, "The GTA VI leak of 2022 — the biggest leak in gaming history"),
    (1143, "The torture scene in 'By the Book'"),
    (1228, "Hacker Arion Kurtaj — breaching Rockstar with a Fire Stick"),
    (1307, "The dark side of NoPixel — lawsuits and pay-to-queue"),
    (1395, "Cancelled 'Agent' and cut GTA V DLC"),
    (1473, "Real copycat tragedies and moral panic"),
    (1565, "Debunked hoaxes — Ratman, Leatherface, Ghost Town"),
]

TITLE = "The GTA ICEBERG — Secrets, Cults, Leaks & the Darkest Truths Rockstar Never Told You"
HOOK = ("Behind Grand Theft Auto's record-breaking success hides a labyrinth of buried secrets, "
        "real crimes and myths that took fans years to crack. From the hunt for Bigfoot in San Andreas "
        "to the biggest leak in gaming history, the Epsilon cult, the teenage hacker who breached "
        "Rockstar with a Fire Stick, and the real tragedies blamed on the game — this is the full "
        "GTA iceberg, from the surface legends down to the coldest, darkest depths.")

TAGS = ["gta iceberg", "grand theft auto iceberg", "gta 6", "gta vi", "gta 5 secrets",
        "gta rp", "nopixel", "gta leak", "arion kurtaj", "rockstar games",
        "gta bigfoot", "mount chiliad", "hot coffee", "epsilon cult", "gta lore",
        "gaming iceberg", "gta dark side", "gta mysteries", "gta documentary", "iceberg explained"]


def tc(s): return f"{int(s // 60):02d}:{int(s % 60):02d}"


def main() -> int:
    # смерджить уровни + темы + заключение по времени
    rows = [(0, "Intro", "intro")]
    for st, n, t in LEVELS:
        rows.append((st, f"LEVEL {n}: {t}", "level"))
    for st, t in TOPICS:
        rows.append((st, t, "topic"))
    rows.append((CONCL, "Conclusion", "concl"))
    rows.sort(key=lambda r: (r[0], {"intro": 0, "level": 1, "topic": 2, "concl": 3}[r[2]]))

    lines = []
    for st, t, k in rows:
        if k == "level":
            lines.append("")
            lines.append(f"{tc(st)} ▬ {t}")
        else:
            lines.append(f"{tc(st)} {t}")

    parts = [TITLE, "", HOOK, "",
             "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", "TIMECODES:"]
    parts += lines
    parts += ["", "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
              "👉 Subscribe for more deep-dive gaming icebergs.", "",
              "TAGS: " + ", ".join(TAGS)]
    txt = "\n".join(parts)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "meta_EN.md").write_text(txt, encoding="utf-8")
    print(f"meta_EN.md → {OUT}")
    print(f"TITLE: {TITLE}")
    print(f"lines: {len(lines)} | topics: {len(TOPICS)} | levels: {len(LEVELS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
