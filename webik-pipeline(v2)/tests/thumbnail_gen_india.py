"""Превью 4К для «Айсберг Индии» — RU (Webik) + EN (Debik). Генерит базовые картинки (без текста)
один раз, затем накладывает PIL-текст двумя языками → RU и EN thumbnails.
  REGEN=1 PYTHONIOENCODING=utf-8 python tests/thumbnail_gen_india.py   # перегенерить картинки
  PYTHONIOENCODING=utf-8 python tests/thumbnail_gen_india.py           # только текст на фикс.картинках
  ONLY=<name> ...
"""
import os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import tests.thumbnail_gen as tg

RU = ROOT / "projects" / "2026-09-22_aysberg-indii-misticheskaya-i-zagadochnaya-storona-strany"
EN = ROOT / "projects" / "2026-09-22_aysberg-indii-misticheskaya-i-zagadochnaya-storona-strany_EN"
REF = Path(r"C:\Users\aidar\OneDrive\Рабочий стол\photo_2025-12-23_21-16-39.jpg")

# индийский триколор-акцент во всех превью (тема = страна)
FLAG = (" In the upper-right corner, a real waving Indian tricolor flag as a bright accent — saffron top "
        "band, white middle band with the navy-blue 24-spoke Ashoka Chakra wheel, green bottom band, "
        "vivid and clearly readable, catching light.")

CONCEPTS = [
    {
        "name": "aghori",
        "subject": (
            "RIGHT HALF: a hyper-realistic documentary photograph of an Aghori ascetic at the ghats of "
            "Varanasi at golden hour — a holy man smeared with grey ash, matted dreadlocks, a "
            "rudraksha-and-bone necklace, forehead marked, holding a human skull, BRIGHTLY lit by warm "
            "golden light with the glow of a pyre behind, intense compelling stare straight at camera, "
            "sharp fine detail, rich warm color, cinematic and striking — looks like a REAL award-winning "
            "National-Geographic photo, not CGI." + FLAG
        ),
    },
    {
        "name": "kali",
        "subject": (
            "RIGHT HALF: a real photograph of a fierce, vividly colored Kali idol in a temple — deep "
            "blue skin, bright red tongue out, wide white eyes, a garland of skulls, many arms with "
            "blades, brightly lit by warm temple lamps and spotlights so every detail pops, gold and rich "
            "red offerings and marigolds, saturated colorful and dramatic, crisp and clear — like a real "
            "vivid temple documentary photo, not CGI." + FLAG
        ),
    },
    {
        "name": "pyre_ghats",
        "subject": (
            "RIGHT HALF: a real documentary photograph of the ghats of Varanasi at sunset — glowing "
            "funeral pyres and warm firelight on the stone steps by the Ganges, colorful sky, silhouettes "
            "of mourners and a sadhu, smoke lit warm-orange, bright vivid reflections on the river, "
            "cinematic, rich saturated color, sharp — a REAL striking photo, not CGI." + FLAG
        ),
    },
]


def main():
    model = os.environ.get("IMG_MODEL", "google/gemini-3-pro-image")
    only = os.environ.get("ONLY")
    regen = bool(os.environ.get("REGEN"))
    ru_dir = RU / "thumbnails"; ru_dir.mkdir(exist_ok=True)
    en_dir = EN / "thumbnails"; en_dir.mkdir(exist_ok=True)
    print(f"модель: {model} | {'ПЕРЕГЕН' if regen else 'только текст'}")
    for c in CONCEPTS:
        if only and c["name"] != only:
            continue
        base = ru_dir / f"{c['name']}_base.png"
        if regen or not base.exists():
            prompt = tg.STYLE + c["subject"] + " " + tg.NO_TEXT
            print(f"[{c['name']}] генерю базу…", flush=True)
            tg.generate_base(prompt, base, REF, model)
        if not base.exists():
            print(f"[{c['name']}] базы нет — пропуск"); continue
        # RU (Webik) + EN (Debik) текст на одной базе
        tg.render_text(base, "АЙСБЕРГ", "ИНДИИ", ru_dir / f"{c['name']}_RU.jpg")
        tg.render_text(base, "ICEBERG", "OF INDIA", en_dir / f"{c['name']}_EN.jpg")
        print(f"[{c['name']}] RU+EN готово", flush=True)
    print("ГОТОВО")


if __name__ == "__main__":
    main()
