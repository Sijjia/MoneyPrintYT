"""Reddit-превью в стиле проверенного GTA-айсберга: ЯРКИЙ полный айсберг + БОЛЬШОЙ окровавленный
оранжевый Reddit-логотип (Snoo) как герой на айсберге + крупное «АЙСБЕРГ/REDDIT» справа-сверху.
Модель рисует всё за один проход (как GTA). RU и EN.
  PYTHONIOENCODING=utf-8 ../webik-pipeline/.venv/Scripts/python.exe tests/thumbnail_reddit2.py
  REGEN=1 ...  — перегенерить."""
import os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tests.thumbnail_gen_gta import generate_base  # noqa

# стиль-референс: уже удачно вышедший GTA-айсберг (тот же вид льда/воды/композиции)
REF = ROOT / "projects" / "2026-09-06_aysberg-gta-temnaya-storona-realnye-dela-vnutriigrovye-tayny" / "thumbnails" / "thumb_iceberg_ru.png"
PROJECT = "2026-09-13_aysberg-reddit-strannaya-i-trevozhnaya-storona"
OUTDIR = ROOT / "projects" / PROJECT / "thumbnails"
MODEL = os.environ.get("IMG_MODEL", "google/gemini-3-pro-image")

BASE = (
    "Create a professional YouTube thumbnail, 16:9, ultra sharp, 4K (3840x2160), in EXACTLY the same "
    "bright vivid iceberg STYLE and composition as the REFERENCE image (same lighting, same saturated "
    "blue water, same sunny sky) — but this is about REDDIT, NOT about games. Style: a BRIGHT, vivid, "
    "photorealistic ICEBERG filling the whole frame — sunny light-blue sky with the white iceberg peak "
    "in the upper-left/center, and the huge submerged mass of ice descending through rich saturated blue "
    "water into deep dark-blue/black depths at the bottom. Clean, high-contrast, saturated, eye-catching "
    "— NOT dark horror, NOT grim, NOT washed-out.\n"
    "HERO ELEMENT: a BIG glossy 3D ORANGE Reddit logo (the Snoo alien mascot — round head with an "
    "antenna, big round eyes, small smile, Reddit's signature bright orange #FF4500) placed PROMINENTLY "
    "on/above the bright peak of the iceberg, LARGE and clearly recognizable as Reddit, SPLATTERED and "
    "DRIPPING with fresh wet red blood running down it. This bloody orange Reddit logo is the main focus.\n"
    "Scattered deeper down the iceberg into the darker depths: a few small glossy Reddit-alien badge "
    "stickers (the Snoo head), smaller and dimmer the deeper they go — like logo stickers on the ice.\n"
    "DO NOT put any game logos. TOP-RIGHT: leave the sky clean for a big title.\n"
    "{title_block}"
    "No watermark. No random extra text besides what is specified."
)
TITLE_RU = ("In the TOP-RIGHT put the word «АЙСБЕРГ» in HUGE bold white uppercase Cyrillic with a thick "
            "black outline and drop shadow (perfectly horizontal, not tilted), and directly BELOW it the "
            "Reddit handle 'r/reddit' written in a stylish, distinctive modern font — the 'r/' part in "
            "Reddit's bright ORANGE (#FF4500) and 'reddit' in clean white, all with a thick black outline "
            "and glossy look, like a cool subreddit tag. Spell АЙСБЕРГ and r/reddit exactly (lowercase "
            "'r/reddit'), no quotation marks. ")
TITLE_EN = ("In the TOP-RIGHT put the word 'ICEBERG' in HUGE bold white uppercase with a thick black "
            "outline and drop shadow (perfectly horizontal, not tilted), and directly ABOVE it the Reddit "
            "handle 'r/reddit' written in a stylish, distinctive modern font — the 'r/' part in Reddit's "
            "bright ORANGE (#FF4500) and 'reddit' in clean white, all with a thick black outline and glossy "
            "look, like a cool subreddit tag. Spell ICEBERG and r/reddit exactly (lowercase 'r/reddit'), "
            "no quotation marks. ")


def main() -> int:
    OUTDIR.mkdir(exist_ok=True)
    regen = bool(os.environ.get("REGEN"))
    ref = REF if REF.exists() else None
    print(f"референс: {'есть' if ref else 'НЕТ (генерю по описанию)'}")
    jobs = [("ru", TITLE_RU, OUTDIR / "thumb_ice2_ru.png"),
            ("en", TITLE_EN, OUTDIR / "thumb_ice2_en.png")]
    for lang, tb, out in jobs:
        if out.exists() and not regen:
            print(f"[{lang}] есть {out.name} — пропуск (REGEN=1)"); continue
        prompt = BASE.format(title_block=tb)
        print(f"[{lang}] генерю {out.name} …", flush=True)
        try:
            generate_base(prompt, out, ref, MODEL)
            print(f"[{lang}] ✓ {out}  ({out.stat().st_size//1024} KB)")
        except Exception as e:
            print(f"[{lang}] ✗ {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
