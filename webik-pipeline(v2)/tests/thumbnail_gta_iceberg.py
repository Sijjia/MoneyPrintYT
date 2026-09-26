"""Превью в стиле референса Айдара (Снимок экрана 2026-09-11): ЯРКИЙ полный айсберг +
лого игр GTA как наклейки по глубине + крупное «АЙСБЕРГ»/«ICEBERG» справа-сверху + лого GTA.
Генерит RU и EN. Nano Banana Pro, скрин Айдара как style-референс.
  PYTHONIOENCODING=utf-8 ../webik-pipeline/.venv/Scripts/python.exe tests/thumbnail_gta_iceberg.py
  REGEN=1 ...  — перегенерить (иначе, если база есть, не трогает)"""
import os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tests.thumbnail_gen_gta import generate_base  # noqa

REF = Path(r"C:\Users\aidar\OneDrive\Рабочий стол\Снимок экрана 2026-09-11 115145.png")
PROJECT = "2026-09-06_aysberg-gta-temnaya-storona-realnye-dela-vnutriigrovye-tayny"
OUTDIR = ROOT / "projects" / PROJECT / "thumbnails"
MODEL = os.environ.get("IMG_MODEL", "google/gemini-3-pro-image")

BASE = (
    "Create a professional YouTube thumbnail, 16:9, ultra sharp, 4K (3840x2160), in EXACTLY the same "
    "style and composition as the REFERENCE image provided. Style: a BRIGHT, vivid, photorealistic "
    "ICEBERG filling the whole frame — sunny light-blue sky with the white iceberg peak in the upper "
    "area, and the huge submerged mass of ice descending through blue water into deep dark-blue/black "
    "depths at the bottom. Clean, high-contrast, saturated, eye-catching gaming-channel look — NOT dark "
    "horror, NOT grim.\n"
    "Scattered ACROSS the iceberg from the sunny peak down into the dark depths: recognizable Grand Theft "
    "Auto game emblems as small glossy rounded stickers/badges — the GTA V logo, the GTA IV logo, the "
    "GTA San Andreas logo, the GTA Vice City logo, the GTA VI logo, and the Rockstar Games 'R★' yellow "
    "star logo. Put the famous/mainstream emblems near the bright top and the darker/obscure ones deep "
    "underwater. Each emblem crisp, clean and correct, like real logo stickers placed on the ice.\n"
    "TOP-RIGHT: leave the sky area clean and uncluttered for a big title that will sit there.\n"
    "{title_block}"
    "No watermark. No random extra text besides what is specified."
)
TITLE_RU = ("In the TOP-RIGHT put the single word «АЙСБЕРГ» in HUGE bold white uppercase Cyrillic with a "
            "thick black outline and drop shadow (perfectly horizontal, not tilted), and directly BELOW it "
            "the official 'grand theft auto' wordmark logo (classic GTA game logo look). Spell АЙСБЕРГ "
            "exactly, no quotation marks. ")
TITLE_EN = ("In the TOP-RIGHT put the single word 'ICEBERG' in HUGE bold white uppercase with a thick "
            "black outline and drop shadow (perfectly horizontal, not tilted), and directly BELOW it the "
            "official 'grand theft auto' wordmark logo (classic GTA game logo look). Spell ICEBERG exactly, "
            "no quotation marks. ")


def main() -> int:
    OUTDIR.mkdir(exist_ok=True)
    regen = bool(os.environ.get("REGEN"))
    if not REF.exists():
        print(f"✗ нет референса {REF}"); return 1
    jobs = [("ru", TITLE_RU, OUTDIR / "thumb_iceberg_ru.png"),
            ("en", TITLE_EN, OUTDIR / "thumb_iceberg_en.png")]
    for lang, tb, out in jobs:
        if out.exists() and not regen:
            print(f"[{lang}] есть {out.name} — пропуск (REGEN=1 для перегена)"); continue
        prompt = BASE.format(title_block=tb)
        print(f"[{lang}] генерю {out.name} …", flush=True)
        try:
            generate_base(prompt, out, REF, MODEL)
            print(f"[{lang}] ✓ {out}  ({out.stat().st_size//1024} KB)")
        except Exception as e:
            print(f"[{lang}] ✗ {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
