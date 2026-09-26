"""RU-описание для «Айсберг GTA» (Webik). Таймкоды с RU-таймлайна (совпадают с alignment 1:1),
тексты плашек = voiceover announce-сцен (ровно что на экране). Пишет meta_RU.md в
E:\\video for ytb\\Webik\\Айсберг GTA\\."""
import sys
from pathlib import Path

OUT = Path(r"E:\video for ytb\Webik\Айсберг GTA")

LINKS = ("https://t.me/webik_studio — НОВОСТИ\n"
         "https://www.donationalerts.com/r/webikstudio — Поддержать, чтобы выходило больше видео")

# level cards (RU-таймлайн)
LEVELS = [(25, 1, "ЛЕГЕНДЫ. СЕКРЕТЫ."), (415, 2, "КУЛЬТЫ. ЗАГОВОРЫ."),
          (781, 3, "РАЗОБЛАЧЕНИЯ. СЛИВЫ."), (1163, 4, "ВЗЛОМЫ. МРАК.")]
CONCL = 1655  # ~27:35 конец контента

# topic cards (start_sec, on-screen voiceover) — RU-таймлайн
TOPICS = [
    (30, "Рекорд трейлера GTA VI и прибыльность GTA V"),
    (93, "Bigfoot в San Andreas — легенда, которую искали годами"),
    (169, "Mount Chiliad — загадочная фреска"),
    (253, "Hot Coffee — скрытая секс-мини-игра"),
    (336, "NoPixel 3.0 — как GTA RP взорвал Twitch (2021)"),
    (419, "Призрак Джолин Крэнли-Эванс (Маунт-Гордо)"),
    (482, "НЛО на 100% и затонувшая тарелка"),
    (544, "Культ «Эпсилон» / Kifflom"),
    (615, "xQc: пять банов на NoPixel → тайное совладение сервером"),
    (693, "Джек Томпсон — крестовый поход против GTA"),
    (785, "Развязка Bigfoot — «The Last One» и Sasquatch"),
    (881, "Infinity Killer / Merle Abrahams"),
    (953, "Rainbow Road — величайшие моменты GTA RP"),
    (1006, "Утечка GTA VI 2022 — крупнейший слив в истории игр"),
    (1087, "Сцена пыток «By the Book»"),
    (1167, "Хакер Arion Kurtaj — взлом Rockstar с Fire Stick"),
    (1241, "Тёмная сторона NoPixel — иски и «плати за очередь»"),
    (1329, "Отменённый «Agent» и вырезанное DLC GTA V"),
    (1402, "Реальные копи-кат трагедии и моральная паника"),
    (1496, "Разоблачённые хоаксы — Ratman, Leatherface, Ghost Town"),
]

TITLE = "АЙСБЕРГ GTA — Секреты, Культы, Сливы и Самая Тёмная Сторона, о Которой Молчит Rockstar"
HOOK = ("За рекордами и миллиардами Grand Theft Auto прячется лабиринт скрытых секретов, реальных "
        "преступлений и мифов, которые фанаты разгадывали годами. От охоты за Бигфутом в Сан-Андреасе "
        "до крупнейшего слива в истории игр, культа «Эпсилон», подростка, взломавшего Rockstar с помощью "
        "Fire Stick, и реальных трагедий, в которых обвиняли игру — это полный айсберг GTA, от легенд "
        "на поверхности до самого холодного и тёмного дна.")

TAGS = ["айсберг gta", "gta айсберг", "gta 6", "gta vi", "секреты gta 5", "gta rp", "nopixel",
        "утечка gta 6", "arion kurtaj", "rockstar games", "бигфут gta", "mount chiliad",
        "hot coffee", "культ эпсилон", "тёмная сторона gta", "тайны gta", "айсберг игры",
        "gta разбор", "grand theft auto", "webik"]


def tc(s): return f"{int(s // 60):02d}:{int(s % 60):02d}"


def main() -> int:
    rows = [(0, "Вступление", "intro")]
    for st, n, t in LEVELS:
        rows.append((st, f"УРОВЕНЬ {n}: {t}", "level"))
    for st, t in TOPICS:
        rows.append((st, t, "topic"))
    rows.append((CONCL, "Заключение", "concl"))
    rows.sort(key=lambda r: (r[0], {"intro": 0, "level": 1, "topic": 2, "concl": 3}[r[2]]))

    lines = []
    for st, t, k in rows:
        if k == "level":
            lines.append("")
            lines.append(f"{tc(st)} ▬ {t}")
        else:
            lines.append(f"{tc(st)} {t}")

    parts = [TITLE, "", HOOK, "", LINKS, "",
             "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", "ТАЙМКОДЫ:"]
    parts += lines
    parts += ["", "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
              "👉 Подпишись, чтобы не пропустить новые айсберги.", "",
              "ТЕГИ: " + ", ".join(TAGS)]
    txt = "\n".join(parts)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "meta_RU.md").write_text(txt, encoding="utf-8")
    print(f"meta_RU.md -> {OUT}")
    print(f"TITLE({len(TITLE)}): {TITLE}")
    print(f"topics {len(TOPICS)} | levels {len(LEVELS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
