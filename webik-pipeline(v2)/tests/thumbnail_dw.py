"""Превью 4К для «Айсберг DreamWorks» — клон thumbnail_gen под тему студии.
База (картинка без текста) генерится один раз; текст RU (АЙСБЕРГ/DREAMWORKS) и EN (ICEBERG/DREAMWORKS)
кладём PIL-ом на ту же базу. Концепты: тёмная луна-с-мальчиком / киноархив / зловещий силуэт.

REGEN=1 — перегенерить базы; ONLY=<name> — один концепт; LANG=ru|en — какой текст (по умолч. оба)."""
import base64, json, mimetypes, os, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from PIL import Image, ImageDraw, ImageFont, ImageFilter  # noqa

FONT_PATH = r"C:\Windows\Fonts\ariblk.ttf"         # АЙСБЕРГ/ICEBERG — Arial Black (жирный геометричный, как референс)
BRAND_FONT = r"C:\Windows\Fonts\georgiab.ttf"      # DreamWorks — засечки, mixed-case «под логотип»
COLOR_TOP = (255, 255, 255)
COLOR_BOT = (226, 8, 8)
W4K, H4K = 3840, 2160
PROJECT = "2026-08-25_aysberg-dreamworks-lost-media-i-temnaya-skrytaya-storona-stu"


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
    im = Image.open(base_path).convert("RGBA")
    if im.size != (W4K, H4K):
        im = im.resize((W4K, H4K), Image.LANCZOS)
    probe = ImageDraw.Draw(im)
    maxw = int(W4K * 0.60)
    f_top = _fit(probe, top, maxw, cap=430)
    f_bot = _fit(probe, bot, maxw, cap=470, font_path=BRAND_FONT)  # бренд-шрифт под логотип
    x = 175                                   # чуть правее (текст не уезжает за край)
    sw_t, sw_b = max(3, f_top.size // 22), max(3, f_bot.size // 22)
    tb = probe.textbbox((0, 0), top, font=f_top, stroke_width=sw_t)
    bb = probe.textbbox((0, 0), bot, font=f_bot, stroke_width=sw_b)
    y_bot = H4K - 235 - (bb[3] - bb[1])       # чуть выше
    y_top = y_bot - (tb[3] - tb[1]) - int(f_top.size * 0.16)
    # ЦЕНТРИРОВАНИЕ друг относительно друга (как КНДР/референс): оба по общему центру cx
    tw, bw = tb[2] - tb[0], bb[2] - bb[0]
    cx = x + max(tw, bw) / 2
    top_xy = (cx - tw / 2 - tb[0], y_top - tb[1])
    bot_xy = (cx - bw / 2 - bb[0], y_bot - bb[1])
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    off = int(W4K * 0.004)
    sd.text((top_xy[0] + off, top_xy[1] + off), top, font=f_top, fill=(0, 0, 0, 200), stroke_width=sw_t, stroke_fill=(0, 0, 0, 200))
    sd.text((bot_xy[0] + off, bot_xy[1] + off), bot, font=f_bot, fill=(0, 0, 0, 200), stroke_width=sw_b, stroke_fill=(0, 0, 0, 200))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(int(W4K * 0.006))))
    d = ImageDraw.Draw(im)
    d.text(top_xy, top, font=f_top, fill=COLOR_TOP, stroke_width=sw_t, stroke_fill=(0, 0, 0))
    d.text(bot_xy, bot, font=f_bot, fill=COLOR_BOT, stroke_width=sw_b, stroke_fill=(0, 0, 0))
    im.convert("RGB").save(out_path, quality=95)
    print(f"  ✎ {top} / {bot}  ({f_top.size}/{f_bot.size}px)")


STYLE = (
    "Professional 4K (3840x2160, strict 16:9) YouTube thumbnail — VIVID, BRIGHT, high-contrast and "
    "eye-catching like a top mystery-documentary channel. PHOTOREALISTIC, looks like a real crisp photo. "
    "LEFT HALF: a massive BRIGHT photorealistic ICEBERG — brilliant cyan/blue ice peak above a bright "
    "teal-blue ocean, and the huge luminous submerged ice mass glowing below the clear waterline; "
    "vivid, sharp, cold but LUMINOUS (NOT dark, NOT grim, NOT near-black). The two halves blend into ONE "
    "seamless continuous image with a SOFT gradual transition in the middle — NO hard vertical line, NO "
    "dark seam band, NO split-screen border; the bright blue flows smoothly across. Punchy cinematic "
    "contrast, saturated, equally bright on both sides. "
)
NO_TEXT = ("ABSOLUTELY NO text, letters, words, captions, numbers or watermark anywhere in the image. "
           "Keep the lower-left area a bit calmer (space reserved for a title added later), but still bright. ")

CONCEPTS = [
    {"name": "dark_moon",
     "subject": ("RIGHT HALF: a dreamy cinematic scene — a child silhouette sitting on a glowing crescent "
                 "moon holding a fishing rod; the crescent moon and the child are LARGE and PROMINENT, "
                 "filling most of the right half (close, big, hero-sized), against a moonlit DEEP-BLUE night "
                 "sky with soft luminous silver clouds and a bright glowing moon casting rim light on the "
                 "child; magical, iconic, clearly VISIBLE and well-lit (a nostalgic homage to a famous "
                 "animation-studio logo), rich blue tones, bright enough to read clearly — NOT dark, no text. ")},
    {"name": "film_vault",
     "subject": ("RIGHT HALF: a dark abandoned film archive — stacks of dusty vintage film reels and metal "
                 "film canisters, one reel unspooled tangled on the floor, a single dim hard raking light, "
                 "deep black shadows, dust in the air, grim forensic-archive realism, desaturated grey-brown. ")},
    {"name": "shadow_brute",
     "subject": ("RIGHT HALF: a menacing hulking shadowy brute figure with broad shoulders looming in "
                 "near-darkness, only a thin rim of cold light along its silhouette, ominous and threatening, "
                 "photoreal cinematic horror, heavily desaturated — a generic monstrous silhouette, not any "
                 "branded character, no text. ")},
]

TEXTS = {"ru": ("АЙСБЕРГ", "DreamWorks"), "en": ("ICEBERG", "DreamWorks")}


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
                render_text(base, top, bot, outdir / f"thumb_{c['name']}_{lg}.png")
        except Exception as e:
            print(f"  ✗ ошибка: {e}")
    print(f"\nпревью в {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
