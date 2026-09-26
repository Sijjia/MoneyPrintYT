"""
Генератор превью (thumbnail) 4К для айсберг-роликов.

ПРАВИЛЬНАЯ архитектура (картинка и текст разделены):
  1) КАРТИНКА генерится ОДИН раз (модель), без текста, и фиксируется как <name>_base.png.
     Правки текста её НЕ трогают. Перегенерить картинку — только с REGEN=1.
  2) ТЕКСТ накладывается отдельно (PIL, единый шрифт, мягкая тень) → мгновенно, стабильно,
     одинаково на всех превью. Поменял слово/размер — перезапустил, картинка та же.

Формула канала (референс photo_2025-12-23): ЛЕВО = фотореалистичный айсберг (над/под водой,
холодный синий); вертикальный шов синий→красный; ПРАВО = тематический «горячий» объект;
низ-слева — крупный белый «АЙСБЕРГ» + тема красным.

Бэкенд картинки — OpenRouter image-модели (OPENROUTER_API_KEY):
  google/gemini-3-pro-image (Nano Banana Pro, дефолт) | openai/gpt-5.4-image-2 (GPTimage 2.0)

Запуск:
  python tests/thumbnail_gen.py            # текст на зафиксированных картинках (картинку не трогает)
  REGEN=1 python tests/thumbnail_gen.py    # перегенерить картинки с нуля
  ONLY=<name> ...                          # только один концепт
  IMG_MODEL=... ...                        # сменить модель
(всегда с PYTHONIOENCODING=utf-8 — иначе консоль cp1251 падает на кириллице)
"""
import base64
import json
import mimetypes
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from PIL import Image, ImageDraw, ImageFont, ImageFilter  # noqa

# ── ЕДИНЫЙ СТИЛЬ ТЕКСТА КАНАЛА (менять тут — меняется на всех превью разом) ────
FONT_PATH = str(ROOT / "assets" / "thumb_fonts" / "RobotoCondensed-Bold.ttf")  # Roboto Condensed Bold — как в опубл. Айсберг ГТА/Reddit (жирный, умеренно узкий, кириллица)
COLOR_TOP = (255, 255, 255)                   # верхнее слово — белое
COLOR_BOT = (226, 8, 8)                       # нижнее слово — красное
W4K, H4K = 3840, 2160
PROJECT = "2026-08-18_aysberg-evolyutsii-temnaya-i-zapretnaya-storona-evolyutsii-o"


# ── картинка (модель) ────────────────────────────────────────────────────────
def _api_key():
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("OPENROUTER_API_KEY не найден в .env")


def _data_url(path: Path):
    mime = mimetypes.guess_type(str(path))[0] or "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def generate_base(prompt: str, out_path: Path, ref: Path | None, model: str):
    """Сгенерить КАРТИНКУ без текста и сохранить как базу (4К)."""
    content = [{"type": "text", "text": prompt}]
    if ref and ref.exists():
        content.append({"type": "image_url", "image_url": {"url": _data_url(ref)}})
    body = {"model": model, "modalities": ["image", "text"],
            "messages": [{"role": "user", "content": content}]}
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {_api_key()}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        data = json.load(r)
    msg = data["choices"][0]["message"]
    imgs = msg.get("images") or [p for p in (msg.get("content") or [])
                                 if isinstance(p, dict) and p.get("type") == "image_url"]
    if not imgs:
        raise RuntimeError(f"модель не вернула изображение: {json.dumps(data)[:400]}")
    raw = base64.b64decode(imgs[0]["image_url"]["url"].split(",", 1)[1])
    out_path.write_bytes(raw)
    im = Image.open(out_path).convert("RGB")
    if im.size != (W4K, H4K):
        im = im.resize((W4K, H4K), Image.LANCZOS)
    im.save(out_path, quality=95)
    print(f"  🖼  база: {out_path.name}")


# ── текст (PIL, чисто и стабильно) ───────────────────────────────────────────
def _fit(draw, text, maxw, cap):
    sz = cap
    while sz > 24:
        f = ImageFont.truetype(FONT_PATH, sz)
        if draw.textlength(text, font=f) <= maxw:
            return f
        sz -= 4
    return ImageFont.truetype(FONT_PATH, sz)


def render_text(base_path: Path, top: str, bot: str, out_path: Path):
    """Наложить текст на ЗАФИКСИРОВАННУЮ картинку (не меняя её): белое слово + красное."""
    im = Image.open(base_path).convert("RGBA")
    if im.size != (W4K, H4K):
        im = im.resize((W4K, H4K), Image.LANCZOS)
    # гарантийный «поярче/поконтрастнее/понасыщеннее» пас (Айдар: превью каждый раз слишком тёмные)
    from PIL import ImageEnhance
    rgb = im.convert("RGB")
    rgb = ImageEnhance.Brightness(rgb).enhance(1.12)
    rgb = ImageEnhance.Contrast(rgb).enhance(1.18)
    rgb = ImageEnhance.Color(rgb).enhance(1.18)
    im = rgb.convert("RGBA")
    probe = ImageDraw.Draw(im)
    # КРУПНЫЙ текст (как «Айсберг ГТА/Reddit»); можно переопределить env-ами
    maxw = int(W4K * float(os.environ.get("TXT_MAXW", "0.56")))
    cap_top = int(os.environ.get("TXT_CAP_TOP", "470"))
    cap_bot = int(os.environ.get("TXT_CAP_BOT", "560"))
    vcenter = float(os.environ.get("TXT_VCENTER", "0.50"))  # доля высоты — центр текстового блока
    f_top = _fit(probe, top, maxw, cap=cap_top)
    f_bot = _fit(probe, bot, maxw, cap=cap_bot)
    x = 110
    sw_t, sw_b = max(3, f_top.size // 20), max(3, f_bot.size // 20)
    tb = probe.textbbox((0, 0), top, font=f_top, stroke_width=sw_t)
    bb = probe.textbbox((0, 0), bot, font=f_bot, stroke_width=sw_b)
    th, bh = tb[3] - tb[1], bb[3] - bb[1]
    gap = int(f_top.size * 0.14)
    block_h = th + gap + bh
    y_top = int(H4K * vcenter - block_h / 2)          # блок центрируем по высоте
    y_bot = y_top + th + gap
    top_xy = (x, y_top - tb[1])
    # нижнее слово центрируем по горизонтальному центру слова АЙСБЕРГ (не уводим вправо)
    top_cx = x + (tb[0] + tb[2]) / 2
    bot_x = top_cx - (bb[0] + bb[2]) / 2
    bot_xy = (bot_x, y_bot - bb[1])

    # мягкая тень (отдельный слой + блюр) — profи-look, а не жёсткий дубль
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    off = int(W4K * 0.004)
    sd.text((top_xy[0] + off, top_xy[1] + off), top, font=f_top, fill=(0, 0, 0, 200),
            stroke_width=sw_t, stroke_fill=(0, 0, 0, 200))
    sd.text((bot_xy[0] + off, bot_xy[1] + off), bot, font=f_bot, fill=(0, 0, 0, 200),
            stroke_width=sw_b, stroke_fill=(0, 0, 0, 200))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(int(W4K * 0.006))))

    # чёткий текст с тонкой чёрной обводкой
    d = ImageDraw.Draw(im)
    d.text(top_xy, top, font=f_top, fill=COLOR_TOP, stroke_width=sw_t, stroke_fill=(0, 0, 0))
    d.text(bot_xy, bot, font=f_bot, fill=COLOR_BOT, stroke_width=sw_b, stroke_fill=(0, 0, 0))
    im.convert("RGB").save(out_path, quality=95)
    print(f"  ✎ текст: {top} / {bot}  (шрифт {Path(FONT_PATH).stem}, {f_top.size}/{f_bot.size}px)")


# ── стиль-преамбула + концепты ───────────────────────────────────────────────
STYLE = (
    "Professional 4K (3840x2160, strict 16:9) YouTube thumbnail. PHOTOREALISTIC documentary "
    "photography — looks like a REAL sharp high-detail photograph, not CGI, not 3D render, not "
    "illustration, not cartoon. BRIGHT, PUNCHY and HIGH-CONTRAST, vivid saturated colors, crisp and "
    "clean, strong dramatic KEY LIGHT hitting the main subject so it POPS and reads instantly even as a "
    "small thumbnail — cinematic but eye-catching, NOT dark, NOT murky, NOT washed-out, NOT muddy. "
    "Composition like the reference: LEFT HALF a massive photorealistic ICEBERG (bright sunlit peak above "
    "a deep-blue ocean and the huge submerged mass below the waterline, vivid turquoise-blue, clearly "
    "visible and well-lit). A vertical seam down the center blends the bright-blue left into a colorful, "
    "well-lit right side where the themed subject is BRIGHTLY lit and fully visible (rich color, strong "
    "highlights, clear detail — never sinking into black). Overall exposure bright and lively. "
)
NO_TEXT = (
    "ABSOLUTELY NO text, letters, words, captions, numbers or watermark anywhere in the image. "
    "Keep the lower-left quarter darker and uncluttered (space reserved for a title added later). "
)
# текст рисует ИИ ПОВЕРХ зафиксированной картинки (режим редактирования — картинка сохраняется)
ADD_TEXT = (
    "Take THIS exact image and ADD ONLY a bold creative YouTube-thumbnail title in the LOWER-LEFT — "
    "do NOT change or regenerate the rest of the picture, keep the iceberg and the right-side subject "
    "identical. Two lines, large heavy uppercase Cyrillic, dramatic and eye-catching (thick strokes, "
    "outline and shadow so it pops): {top} in pure white on top (make it BIG), and below it {bot} "
    "in bright red. Both lines PERFECTLY HORIZONTAL and straight, level baseline, left-aligned — "
    "NOT tilted, NOT slanted, NOT italic, NOT rotated, NOT in perspective. Keep the WHOLE title "
    "comfortably INSIDE the frame with clear margins — never cut any letter off the edge. Spell exactly "
    "{top} and {bot} — plain words with NO quotation marks or guillemets. No other text or watermark."
)
CONCEPTS = [
    {
        "name": "ancestor_face",
        "subject": (
            "RIGHT HALF: a hyper-realistic photograph of the face of an extinct human ancestor "
            "(Neanderthal / archaic human, heavy brow ridge, weathered skin, matted hair, coarse beard), "
            "emerging from near-total darkness, only one side of the face lit by a dim cold light, intense "
            "haunting hollow stare directly at camera, dirt and grime, museum-grade reconstruction realism, "
            "grim, desaturated, terrifyingly real — like a real documentary photo, not CGI. "
        ),
        "top": "АЙСБЕРГ", "bot": "ЭВОЛЮЦИИ",
    },
    {
        "name": "cordyceps_macro",
        "subject": (
            "RIGHT HALF: a real macro NATURE PHOTOGRAPH of a dead ant clamped onto a twig with a single "
            "cordyceps fungus stalk grown out of its head, fine realistic detail, damp dark rainforest "
            "floor, moody low light, shallow depth of field, grim naturalist body-horror, muted earthy "
            "desaturated tones (NO neon, NO glow) — looks like a real BBC-documentary macro shot. "
        ),
        "top": "АЙСБЕРГ", "bot": "ЭВОЛЮЦИИ",
    },
    {
        "name": "skulls_dark",
        "subject": (
            "RIGHT HALF: a real photograph of a row of hominin skulls (ape-like to modern human) on a "
            "dark forensic table, near-darkness, one single dim hard top light raking across them, deep "
            "black shadows, dust in the air, one skull cracked, cold archival/forensic realism, "
            "desaturated grey-brown tones, grim and quiet — like a real museum archive photo. "
        ),
        "top": "АЙСБЕРГ", "bot": "ЭВОЛЮЦИИ",
    },
]


def main():
    ref = Path(r"C:\Users\aidar\OneDrive\Рабочий стол\photo_2025-12-23_21-16-39.jpg")
    outdir = ROOT / "projects" / PROJECT / "thumbnails"
    outdir.mkdir(exist_ok=True)
    model = os.environ.get("IMG_MODEL", "google/gemini-3-pro-image")
    only = os.environ.get("ONLY")
    regen = bool(os.environ.get("REGEN"))
    print(f"модель: {model} | режим: {'ПЕРЕГЕН картинок' if regen else 'только текст (картинки фикс.)'}")
    for c in CONCEPTS:
        if only and c["name"] != only:
            continue
        base = outdir / f"thumb_{c['name']}_base.png"
        final = outdir / f"thumb_{c['name']}.png"
        engine = os.environ.get("TEXT", "ai")   # ai = текст рисует модель поверх базы; pil = наш шрифт
        print(f"\n[{c['name']}]  текст: {engine}")
        try:
            if regen or not base.exists():
                generate_base(STYLE + c["subject"] + NO_TEXT, base, ref, model)
            else:
                print("  🖼  база зафиксирована — не трогаю")
            if engine == "pil":
                render_text(base, c["top"], c["bot"], final)
            else:
                # ИИ дорисовывает текст поверх той же картинки (картинку не пересобирает)
                generate_base(ADD_TEXT.format(top=c["top"], bot=c["bot"]), final, base, model)
                print(f"  ✎ текст (ИИ): {c['top']} / {c['bot']}")
        except Exception as e:
            print(f"  ✗ ошибка: {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
