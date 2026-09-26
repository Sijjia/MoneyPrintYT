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
FONT_PATH = r"C:\Windows\Fonts\seguibl.ttf"   # Segoe UI Black, полная кириллица
COLOR_TOP = (255, 255, 255)                   # верхнее слово — белое
COLOR_BOT = (226, 8, 8)                       # нижнее слово — красное
W4K, H4K = 3840, 2160
PROJECT = "2026-09-06_aysberg-gta-temnaya-storona-realnye-dela-vnutriigrovye-tayny"


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
    probe = ImageDraw.Draw(im)
    maxw = int(W4K * 0.52)
    f_top = _fit(probe, top, maxw, cap=350)
    f_bot = _fit(probe, bot, maxw, cap=420)
    x = 120
    sw_t, sw_b = max(3, f_top.size // 22), max(3, f_bot.size // 22)
    tb = probe.textbbox((0, 0), top, font=f_top, stroke_width=sw_t)
    bb = probe.textbbox((0, 0), bot, font=f_bot, stroke_width=sw_b)
    y_bot = H4K - 150 - (bb[3] - bb[1])
    y_top = y_bot - (tb[3] - tb[1]) - int(f_top.size * 0.16)
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
    "photography — looks like a REAL photograph, not CGI, not 3D render, not illustration, not cartoon. "
    "DARK and GRIM mood: low-key lighting, heavy deep shadows, muted desaturated colors, subtle film "
    "grain, cold and unsettling, cinematic horror-documentary. NO neon, NO glowing saturated colors, "
    "NO glossy plastic look. Composition like the reference: LEFT HALF a massive photorealistic ICEBERG "
    "(peak above the near-black ocean and the huge submerged mass below the waterline, cold desaturated "
    "blue-grey, very dark). A subtle vertical seam down the center blends the cold-dark-blue left into a "
    "shadow-heavy, near-black right side lit by a single dim hard light (grim, cold, understated — NOT "
    "bright, NOT crimson, NOT neon). "
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
        "name": "neon_city",
        "subject": (
            "RIGHT HALF: a hyper-realistic cinematic night shot of a GTA-style neon city skyline (Los Santos "
            "vibe), palm trees, purple and pink neon glow, wet streets reflecting lights, a lone hooded "
            "figure in silhouette, moody rain, film-grain realism, GTA VI atmosphere — looks like a real "
            "cinematic still, not a game render. "
        ),
        "top": "АЙСБЕРГ", "bot": "GTA",
    },
    {
        "name": "masked",
        "subject": (
            "RIGHT HALF: a hyper-realistic photograph of a person in a menacing ski mask / robber mask, "
            "dark hoodie, holding a pistol low, lit only by cold neon rim light from the side, near-total "
            "darkness around, grimy criminal underworld mood, intense and threatening, desaturated with a "
            "hint of neon — real gritty photo realism, not CGI. "
        ),
        "top": "АЙСБЕРГ", "bot": "GTA",
    },
    {
        "name": "money_gun",
        "subject": (
            "RIGHT HALF: a real photograph of stacks of cash and a handgun on a dark table under a single "
            "cold neon light, scattered bills, deep black shadows, criminal-underworld still-life, grim and "
            "moody, desaturated with neon accent — looks like a real crime-scene / documentary photo. "
        ),
        "top": "АЙСБЕРГ", "bot": "GTA",
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
