"""Превью 4К для «Айсберг Adult Swim» — клон thumbnail под тему ночного блока CN.
База (картинка без текста) генерится один раз; текст RU (АЙСБЕРГ/adult swim) и EN (ICEBERG/adult swim)
кладём PIL-ом на ту же базу. Концепты: жуткий ночной CRT / LED-Mooninite из Бостона / силуэт из помех.

REGEN=1 — перегенерить базы; ONLY=<name> — один концепт; THUMB_LANG=ru|en — какой текст (по умолч. оба)."""
import base64, json, mimetypes, os, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from PIL import Image, ImageDraw, ImageFont, ImageFilter  # noqa

FONT_PATH = r"C:\Windows\Fonts\ariblk.ttf"         # АЙСБЕРГ/ICEBERG — Arial Black
BRAND_FONT = r"C:\Windows\Fonts\arialbd.ttf"       # adult swim — плоский жирный сан (как бампер-лого)
COLOR_TOP = (255, 255, 255)
COLOR_BOT = (226, 8, 8)
W4K, H4K = 3840, 2160
PROJECT = "2026-08-31_aysberg-adult-swim-temnaya-skrytaya-storona-nochnogo-bloka-c"
# Папка выгрузки видео — превью кладём СЮДА ЖЕ (рядом с mp4), чтобы не бегать между папками.
EXPORT_DIR = Path(r"E:\video for ytb\Webik\Айсберг Adult Swim")
EXPORT_NAME = "Айсберг Adult Swim"   # превью назовём как видео: <name>_RU.png / _EN.png


def _api_key():
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("OPENROUTER_API_KEY не найден в .env")


def _data_url(path: Path):
    mime = mimetypes.guess_type(str(path))[0] or "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def generate_base(prompt: str, out_path: Path, ref: Path | None, model: str):
    content = [{"type": "text", "text": prompt}]
    if ref and ref.exists():
        content.append({"type": "image_url", "image_url": {"url": _data_url(ref)}})
    body = {"model": model, "modalities": ["image", "text"],
            "messages": [{"role": "user", "content": content}]}
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {_api_key()}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        data = json.load(r)
    msg = data["choices"][0]["message"]
    imgs = msg.get("images") or [p for p in (msg.get("content") or [])
                                 if isinstance(p, dict) and p.get("type") == "image_url"]
    if not imgs:
        raise RuntimeError(f"нет изображения: {json.dumps(data)[:300]}")
    raw = base64.b64decode(imgs[0]["image_url"]["url"].split(",", 1)[1])
    out_path.write_bytes(raw)
    im = Image.open(out_path).convert("RGB")
    if im.size != (W4K, H4K):
        im = im.resize((W4K, H4K), Image.LANCZOS)
    im.save(out_path, quality=95)
    print(f"  🖼  база: {out_path.name}")


def _fit(draw, text, maxw, cap, font_path=FONT_PATH):
    sz = cap
    while sz > 24:
        f = ImageFont.truetype(font_path, sz)
        if draw.textlength(text, font=f) <= maxw:
            return f
        sz -= 4
    return ImageFont.truetype(font_path, sz)


def render_text(base_path: Path, top: str, bot: str, out_path: Path):
    """top = АЙСБЕРГ/ICEBERG (белый), bot = бренд → фирменный логотип «[adult swim]»
    (белым на чёрной скруглённой плашке, как в бамперах Adult Swim)."""
    im = Image.open(base_path).convert("RGBA")
    if im.size != (W4K, H4K):
        im = im.resize((W4K, H4K), Image.LANCZOS)
    probe = ImageDraw.Draw(im)
    maxw = int(W4K * 0.60)
    x = 175
    f_top = _fit(probe, top, maxw, cap=430)
    sw_t = max(3, f_top.size // 22)

    # --- бренд-логотип «[adult swim]» (острый чёрный бейдж, БЕЗ скругления/обводки, лёгкий наклон 8° влево) ---
    TILT = 8
    brand = f"[{bot.strip().lower()}]"
    f_bot = _fit(probe, brand, int(W4K * 0.50), cap=300, font_path=BRAND_FONT)
    bb = probe.textbbox((0, 0), brand, font=f_bot)
    bw, bh = bb[2] - bb[0], bb[3] - bb[1]
    pad_x, pad_y = int(f_bot.size * 0.45), int(f_bot.size * 0.30)
    badge_w, badge_h = bw + pad_x * 2, bh + pad_y * 2

    tb = probe.textbbox((0, 0), top, font=f_top, stroke_width=sw_t)
    tw = tb[2] - tb[0]
    cx = x + max(tw, badge_w) / 2

    # острый бейдж на отдельном слое → лёгкий поворот влево
    badge = Image.new("RGBA", (badge_w, badge_h), (0, 0, 0, 0))
    bd = ImageDraw.Draw(badge)
    bd.rectangle([0, 0, badge_w - 1, badge_h - 1], fill=(0, 0, 0, 255))
    bd.text((badge_w / 2, badge_h / 2), brand, font=f_bot, fill=(255, 255, 255), anchor="mm")
    badge = badge.rotate(TILT, expand=True, resample=Image.BICUBIC)

    off = int(W4K * 0.004)
    # вертикали как раньше: бейдж внизу, АЙСБЕРГ прямо над ним (НЕ поднимаем вверх)
    bar_y1 = H4K - 150
    badge_cy = bar_y1 - badge_h / 2
    y_top = (badge_cy - badge_h / 2) - (tb[3] - tb[1]) - int(f_top.size * 0.16)
    top_xy = (cx - tw / 2 - tb[0], y_top - tb[1])

    # тень АЙСБЕРГ
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.text((top_xy[0] + off, top_xy[1] + off), top, font=f_top, fill=(0, 0, 0, 200),
            stroke_width=sw_t, stroke_fill=(0, 0, 0, 200))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(int(W4K * 0.006))))
    d = ImageDraw.Draw(im)
    d.text(top_xy, top, font=f_top, fill=COLOR_TOP, stroke_width=sw_t, stroke_fill=(0, 0, 0))

    # мягкая тень под наклонным бейджем + сам бейдж (центр по cx/badge_cy)
    paste_x = int(cx - badge.width / 2)
    paste_y = int(badge_cy - badge.height / 2)
    bsh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    bsh.paste((0, 0, 0, 150), (paste_x + off, paste_y + off), badge)
    im = Image.alpha_composite(im, bsh.filter(ImageFilter.GaussianBlur(int(W4K * 0.004))))
    im.alpha_composite(badge, (paste_x, paste_y))
    im.convert("RGB").save(out_path, quality=95)
    print(f"  ✎ {top} / {brand}  ({f_top.size}/{f_bot.size}px, наклон {TILT}°)")


STYLE = (
    "Professional 4K (3840x2160, strict 16:9) YouTube thumbnail — VIVID, high-contrast and eye-catching "
    "like a top mystery-documentary channel. PHOTOREALISTIC, looks like a real crisp photo. "
    "LEFT HALF: a massive photorealistic ICEBERG — a brilliant cyan/blue ice peak above a teal-blue ocean, "
    "and the huge luminous submerged ice mass glowing below the clear waterline; sharp, cold but luminous. "
    "The two halves blend into ONE seamless continuous image with a SOFT gradual transition in the middle "
    "— NO hard vertical line, NO split-screen border. Punchy cinematic contrast, saturated. "
)
NO_TEXT = ("ABSOLUTELY NO text, letters, words, captions, numbers, logos or watermark anywhere in the image. "
           "Keep the lower-left area a bit calmer (space reserved for a title added later). ")

CONCEPTS = [
    {"name": "crt_night",
     "subject": ("RIGHT HALF: a vintage 1990s CRT television glowing alone in a pitch-dark room after "
                 "midnight, its screen filled with eerie analog-horror static and a faint distorted ghostly "
                 "face barely emerging from the noise, sickly green-and-cyan screen glow spilling onto the "
                 "dark room, unsettling late-night-TV dread, photoreal, sharp, cinematic, no text. ")},
    {"name": "mooninite_led",
     "subject": ("RIGHT HALF: a glowing Lite-Brite-style LED sign device — a crude pixelated green cartoon "
                 "alien made of colored light bulbs, mounted in the dark under a city overpass at night, "
                 "menacing and mysterious, cyan-green LED glow, photoreal urban night scene (evoking the "
                 "2007 Boston LED-sign panic), sharp and iconic, no text. ")},
    {"name": "static_silhouette",
     "subject": ("RIGHT HALF: a creepy human silhouette figure standing still and emerging out of heavy TV "
                 "static and glitch distortion, faceless, backlit by a cold cyan glow, analog-horror night "
                 "dread, photoreal cinematic, heavily textured with scanlines, ominous, no text. ")},
    {"name": "as_toons",
     "subject": ("RIGHT HALF (fill it, HUGE and prominent, hero-sized): a dark, eerie group lineup of iconic "
                 "Adult Swim cartoon characters glowing ominously against a black late-night-TV background "
                 "with faint scanlines. Include, big and clearly readable: a cynical mad scientist with "
                 "spiky pale-blue hair, a unibrow, and a white lab coat; a trio of anthropomorphic fast-food "
                 "characters — a floating red carton of french fries with a face, a tall white milkshake cup "
                 "with a face and a bendy straw, and a small round brown meatball blob; a chubby balding "
                 "cartoon sitcom dad with round glasses, a big prominent chin, a white short-sleeve shirt "
                 "and green trousers (crudely drawn, deadpan); and two blocky 8-bit pixelated green aliens "
                 "made of glowing colored squares. Flat 2D cartoon animation style but lit dark and moody "
                 "with sinister rim light, unsettling grim mood, crisp and vivid, no text, no watermark. ")},
]

TEXTS = {"ru": ("АЙСБЕРГ", "ADULT SWIM"), "en": ("ICEBERG", "ADULT SWIM")}


def main():
    ref = Path(r"C:\Users\aidar\OneDrive\Рабочий стол\photo_2025-12-23_21-16-39.jpg")
    outdir = ROOT / "projects" / PROJECT / "thumbnails"
    outdir.mkdir(exist_ok=True)
    model = os.environ.get("IMG_MODEL", "google/gemini-3-pro-image")
    only = os.environ.get("ONLY")
    regen = bool(os.environ.get("REGEN"))
    langs = [os.environ["THUMB_LANG"]] if os.environ.get("THUMB_LANG") else ["ru", "en"]
    print(f"модель: {model} | {'ПЕРЕГЕН баз' if regen else 'только текст'} | языки: {langs}")
    for c in CONCEPTS:
        if only and c["name"] != only:
            continue
        base = outdir / f"thumb_{c['name']}_base.png"
        print(f"\n[{c['name']}]")
        try:
            if regen or not base.exists():
                generate_base(STYLE + c["subject"] + NO_TEXT, base, ref, model)
            else:
                print("  🖼  база зафиксирована")
            for lg in langs:
                top, bot = TEXTS[lg]
                out = outdir / f"thumb_{c['name']}_{lg}.png"
                render_text(base, top, bot, out)
                # выбранный концепт (ONLY=<name>) → сразу в папку выгрузки видео, имя как у mp4
                if only and c["name"] == only:
                    try:
                        import shutil
                        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
                        dst = EXPORT_DIR / f"{EXPORT_NAME}_{lg.upper()}.png"
                        shutil.copy(out, dst)
                        print(f"  → в папку видео: {dst.name}")
                    except Exception as e:
                        print(f"  ✗ копия в EXPORT_DIR: {e}")
        except Exception as e:
            print(f"  ✗ ошибка: {e}")
    print(f"\nпревью в {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
