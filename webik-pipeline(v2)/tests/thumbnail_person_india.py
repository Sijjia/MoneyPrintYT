"""Превью в стиле референса «Айсберг Китая»: айсберг слева МЯГКО перетекает в БОЛЬШОЙ флаг Индии,
справа — РЕАЛЬНОЕ фото личности (rembg-вырезка, не ИИ). Композит + текст. Реалистично, лаконично.
  PYTHONIOENCODING=utf-8 python tests/thumbnail_person_india.py            # текст на фикс.bg+персона
  REGEN=1 ... # перегенерить фон
Env: PERSON=<путь к фото>, ONLY=<name>
"""
import os, sys
from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import tests.thumbnail_gen as tg

RU = ROOT / "projects" / "2026-09-22_aysberg-indii-misticheskaya-i-zagadochnaya-storona-strany"
EN = ROOT / "projects" / "2026-09-22_aysberg-indii-misticheskaya-i-zagadochnaya-storona-strany_EN"
W, H = tg.W4K, tg.H4K

# фон: айсберг слева → большой флаг Индии справа, БЕЗ жёсткого деления, без людей и текста
BG_PROMPT = (
    "Photorealistic 4K (3840x2160, 16:9) YouTube thumbnail BACKGROUND — a REAL photograph look, sharp, "
    "bright, high-contrast, vivid, clean and simple. LEFT SIDE: a CLASSIC dramatic ICEBERG shown BOTH "
    "above AND below the waterline — a bright sunlit jagged white-blue peak above the sea surface, and the "
    "MUCH larger glowing ice mass visible underwater through clear deep-blue water below the waterline "
    "(the iconic 'tip of the iceberg' look, like a professional stock photo), crisp detail, a clear "
    "horizon waterline across the left. It blends SMOOTHLY and SOFTLY (NO hard vertical line, NO split, a "
    "gentle gradient) into a HUGE waving INDIAN TRICOLOR FLAG that fills the right two-thirds: saffron top "
    "band, white middle band with the navy-blue 24-spoke Ashoka Chakra wheel, green bottom band, soft "
    "realistic fabric folds, brightly lit and saturated. Leave the RIGHT side reasonably open (a person "
    "will be added there later), lower-left a little calmer for a title. ABSOLUTELY NO text, letters, "
    "numbers, people or watermark."
)


def cutout(person_path: Path) -> Image.Image:
    from rembg import remove
    src = Image.open(person_path).convert("RGBA")
    out = remove(src)  # RGBA с альфой
    # обрезать по bbox непрозрачного
    bbox = out.getbbox()
    if bbox:
        out = out.crop(bbox)
    return out


def compose(bg: Image.Image, person: Image.Image) -> Image.Image:
    bg = bg.convert("RGBA").resize((W, H), Image.LANCZOS)
    # немного поярче фон (гарантия)
    b = bg.convert("RGB")
    b = ImageEnhance.Brightness(b).enhance(1.08)
    b = ImageEnhance.Contrast(b).enhance(1.14)
    b = ImageEnhance.Color(b).enhance(1.14)
    bg = b.convert("RGBA")

    # масштаб персоны: КАП ПО ШИРИНЕ (~50% кадра) → фигура СПРАВА, покрупнее, не в центре.
    pw = int(W * float(os.environ.get("PERSON_W", "0.50")))
    ph = int(person.height * pw / person.width)
    maxh = int(H * 1.02)
    if ph > maxh:
        ph = maxh; pw = int(person.width * ph / person.height)
    person = person.resize((pw, ph), Image.LANCZOS)
    # лёгкая резкость персоне (качество)
    person_rgb = ImageEnhance.Sharpness(person.convert("RGB")).enhance(1.35)
    person = Image.merge("RGBA", (*person_rgb.split(), person.split()[3]))
    # позиция: прижат к ПРАВОМУ краю, стоит на нижней кромке
    px = W - pw + int(W * 0.01)
    py = H - ph

    # мягкая тень-подложка под персоной (объём, отрыв от флага)
    sh = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    alpha = person.split()[3]
    shadow = Image.new("RGBA", person.size, (0, 0, 0, 150))
    shadow.putalpha(alpha)
    sh.paste(shadow, (px + int(W * 0.006), py + int(H * 0.006)), shadow)
    sh = sh.filter(ImageFilter.GaussianBlur(int(W * 0.007)))
    bg = Image.alpha_composite(bg, sh)
    bg.paste(person, (px, py), person)

    # ТЁМНЫЙ градиент по ЛЕВОЙ части (во всю высоту) под КРУПНЫЙ центрированный текст — numpy
    import numpy as np
    _, xx = np.mgrid[0:H, 0:W].astype("float32")
    fx = np.clip(1 - xx / (W * 0.56), 0, 1)            # темнее к левому краю, гаснет к центру
    a = (180 * (fx ** 1.25)).astype("uint8")
    dark = Image.fromarray(np.dstack([np.zeros_like(a)] * 3 + [a]), "RGBA")
    bg = Image.alpha_composite(bg, dark)
    return bg


def main():
    model = os.environ.get("IMG_MODEL", "google/gemini-3-pro-image")
    only = os.environ.get("ONLY")
    regen = bool(os.environ.get("REGEN"))
    person_path = Path(os.environ.get("PERSON", str(ROOT / "remotion" / "public" / "portraits" / "asaram.jpg")))
    name = os.environ.get("NAME", "person")
    ru_dir = RU / "thumbnails"; ru_dir.mkdir(exist_ok=True)
    en_dir = EN / "thumbnails"; en_dir.mkdir(exist_ok=True)

    bg_base = ru_dir / f"bg_flag_base.png"
    if regen or not bg_base.exists():
        print("генерю фон (айсберг+флаг)…", flush=True)
        tg.generate_base(BG_PROMPT, bg_base, None, model)
    assert bg_base.exists(), "нет фона"

    print(f"вырезаю персону: {person_path.name}", flush=True)
    person = cutout(person_path)
    comp = compose(Image.open(bg_base), person)
    comp_path = ru_dir / f"{name}_flag_comp.png"
    comp.convert("RGB").save(comp_path, quality=95)
    print(f"композит: {comp_path.name}", flush=True)

    # текст поверх композита — шрифт Roboto Condensed Bold, но САБСЕТЫ разные:
    # кириллица для RU (латиницы в нём нет → EN был бы квадратами), латиница для EN.
    FONTS = ROOT / "assets" / "thumb_fonts"
    tg.FONT_PATH = str(FONTS / "RobotoCondensed-Bold.ttf")          # cyrillic
    tg.render_text(comp_path, "АЙСБЕРГ", "ИНДИИ", ru_dir / f"{name}_flag_RU.jpg")
    tg.FONT_PATH = str(FONTS / "RobotoCondensed-Bold-Latin.ttf")    # latin
    tg.render_text(comp_path, "ICEBERG", "OF INDIA", en_dir / f"{name}_flag_EN.jpg")
    print("ГОТОВО RU+EN")


if __name__ == "__main__":
    main()
