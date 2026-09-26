"""Шортсы (8 RU + 8 EN) из готовых mp4: LLM выбирает 8 тем + хук-подписи, режем сегмент с титра темы,
9:16 (размытый фон + вписка 16:9 + подпись сверху), ЛОГИЧНАЯ концовка = брендовая CTA-карточка (плавный приход).
→ E:\\...\\Shorts\\ + shorts_meta_RU/EN.md."""
import json, subprocess, sys, textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.llm.claude import ClaudeService
from PIL import Image, ImageDraw, ImageFont

RU_PROJ = ROOT / "projects" / "2026-08-25_aysberg-dreamworks-lost-media-i-temnaya-skrytaya-storona-stu"
SCRATCH = Path(r"C:\Users\aidar\AppData\Local\Temp\claude\C--Users-aidar-OneDrive--------------automotization-youtube\0a3edf5b-8f55-4b33-a918-972784adb4ef\scratchpad")
OUTDIR = Path(r"E:\video for ytb\Webik\Айсберг DreamWorks")
SHORTS = OUTDIR / "Shorts"
SRC = {"ru": OUTDIR / "Айсберг DreamWorks_RU.mp4", "en": OUTDIR / "Айсберг DreamWorks_EN.mp4"}
FONT = r"C:\Windows\Fonts\ariblk.ttf"
W, H = 1080, 1920
VID_W = 1080
VID_H = int(VID_W * 9 / 16)      # 608
VID_Y = (H - VID_H) // 2         # центр
EC_LEN = 2.8                     # длина концовки-карточки
THUMB = {"ru": RU_PROJ / "thumbnails" / "thumb_dark_moon_ru.png",
         "en": RU_PROJ / "thumbnails" / "thumb_dark_moon_en.png"}
# (title сверху, handle снизу, sub под handle)
ENDCARD = {"ru": ("СМОТРИ ПОЛНЫЙ РАЗБОР", "@WebikStudio", "ВЕСЬ АЙСБЕРГ — НА КАНАЛЕ"),
           "en": ("WATCH THE FULL BREAKDOWN", "@Debik", "FULL ICEBERG ON THE CHANNEL")}


def caption_png(text: str, dst: Path):
    im = Image.new("RGBA", (W, VID_Y - 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    size = 78
    while size > 34:
        f = ImageFont.truetype(FONT, size)
        wrapped = textwrap.fill(text, width=max(10, int(W / (size * 0.62))))
        bb = d.multiline_textbbox((0, 0), wrapped, font=f, stroke_width=size // 12, align="center")
        if bb[3] - bb[1] <= im.height - 60 and bb[2] - bb[0] <= W - 80:
            break
        size -= 4
    f = ImageFont.truetype(FONT, size)
    wrapped = textwrap.fill(text, width=max(10, int(W / (size * 0.62))))
    bb = d.multiline_textbbox((0, 0), wrapped, font=f, stroke_width=size // 12, align="center")
    tx = (W - (bb[2] - bb[0])) / 2 - bb[0]
    ty = im.height - (bb[3] - bb[1]) - 30 - bb[1]
    d.multiline_text((tx, ty), wrapped, font=f, fill=(255, 255, 255, 255),
                     stroke_width=size // 12, stroke_fill=(0, 0, 0, 255), align="center", spacing=10)
    im.save(dst)


def _fit_center(d, text, font_path, cap, maxw, stroke):
    sz = cap
    while sz > 26:
        f = ImageFont.truetype(font_path, sz)
        if d.textlength(text, font=f) <= maxw:
            return f
        sz -= 3
    return ImageFont.truetype(font_path, sz)


def _ctext(d, im, cy, text, font, fill, stroke=5):
    bb = d.textbbox((0, 0), text, font=font, stroke_width=stroke)
    d.text(((W - (bb[2] - bb[0])) / 2 - bb[0], cy - (bb[3] - bb[1]) / 2 - bb[1]), text, font=font,
           fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))


def endcard_clip(lang: str, dst_mp4: Path):
    """Премиальная концовка: превью ролика (айсберг+бренд) в центре + размытый фон + CTA. 9:16, фейд-ин, тишина."""
    from PIL import ImageFilter
    img = dst_mp4.with_suffix(".png")
    title, handle, sub = ENDCARD[lang]
    th = THUMB[lang]
    if th.exists():
        src = Image.open(th).convert("RGB")
        # размытый фон (cover) + затемнение
        bg = src.resize((W, int(W * src.height / src.width)), Image.LANCZOS)
        if bg.height < H:
            bg = src.resize((int(H * src.width / src.height), H), Image.LANCZOS)
        left = (bg.width - W) // 2; top = (bg.height - H) // 2
        bg = bg.crop((left, top, left + W, top + H)).filter(ImageFilter.GaussianBlur(34))
        bg = Image.eval(bg, lambda p: int(p * 0.42))
        im = bg.convert("RGB")
        # превью-вставка по центру (16:9)
        fit = src.resize((VID_W, VID_H), Image.LANCZOS)
        im.paste(fit, (0, VID_Y))
    else:
        im = Image.new("RGB", (W, H), (10, 16, 30))
    d = ImageDraw.Draw(im)
    # рамка-подсветка вокруг превью
    d.rectangle([2, VID_Y - 3, W - 3, VID_Y + VID_H + 2], outline=(226, 8, 8), width=6)
    # CTA сверху
    ft = _fit_center(d, title, FONT, 78, W - 120, 6)
    _ctext(d, im, int(H * 0.20), title, ft, (255, 255, 255), 6)
    fa = ImageFont.truetype(FONT, 26)
    _ctext(d, im, int(H * 0.20) + 78, sub, fa, (150, 200, 245), 3)
    # канал снизу
    fh = _fit_center(d, handle, FONT, 78, W - 160, 6)
    _ctext(d, im, int(H * 0.82), handle, fh, (226, 8, 8), 6)
    im.save(img)
    subprocess.run(["ffmpeg", "-y", "-loop", "1", "-t", f"{EC_LEN}", "-i", str(img),
                    "-f", "lavfi", "-t", f"{EC_LEN}", "-i", "anullsrc=r=48000:cl=stereo",
                    "-vf", "fade=t=in:st=0:d=0.4,fps=30,format=yuv420p,setsar=1", "-c:v", "libx264", "-preset", "veryfast",
                    "-crf", "20", "-c:a", "aac", "-ar", "48000", "-ac", "2", "-shortest", str(dst_mp4)],
                   capture_output=True)
    img.unlink(missing_ok=True)
    return dst_mp4.exists()


def end_dur(src: Path, start: float, target: float) -> float:
    """Длительность до естественного стыка (dip-to-black) рядом с target."""
    import re
    win0 = start + max(15.0, target - 8.0)
    r = subprocess.run(["ffmpeg", "-ss", f"{win0:.2f}", "-t", "16", "-i", str(src),
                        "-vf", "blackdetect=d=0.15:pix_th=0.06", "-an", "-f", "null", "-"],
                       capture_output=True, text=True)
    abss = [win0 + float(m) for m in re.findall(r"black_start:(\d+\.?\d*)", r.stderr)]
    cand = [a for a in abss if a - start >= 20.0]
    if cand:
        return min(cand, key=lambda a: abs(a - (start + target))) - start - 0.15  # стоп на последнем кадре до чёрного
    return target


# голос, СИНХРОННЫЙ своему mp4 (RU — выгружен с урезанного таймлайна, EN — не резался): delta=0 для обоих
VOICE = {"ru": RU_PROJ / "assets" / "voice" / "voice_timeline_ru.mp3",
         "en": RU_PROJ.parent / "2026-08-25_aysberg-dreamworks-lost-media-i-temnaya-skrytaya-storona-stu_EN" / "assets" / "voice" / "full.mp3"}


def voice_pause_end(voice: Path, start: float, target: float, delta: float, src: Path) -> float:
    """Конец на паузе в голосе по ЧИСТОЙ дорожке. delta = voice_time - mp4_time (учёт трима).
    Ищем silence рядом с целью в voice-времени, возвращаем длину в mp4-времени."""
    import re
    center = start + delta + target
    win0 = max(0.0, center - 16.0)
    # многопорог: длинная пауза (конец предложения) → короче (меж фраз/вдох). Лишь бы НЕ посреди слова.
    for nz, dd in (("-40", "0.40"), ("-36", "0.30"), ("-32", "0.22"), ("-28", "0.18"), ("-24", "0.16"), ("-21", "0.16")):
        r = subprocess.run(["ffmpeg", "-ss", f"{win0:.2f}", "-t", "34", "-i", str(voice),
                            "-af", f"silencedetect=noise={nz}dB:d={dd}", "-f", "null", "-"],
                           capture_output=True, text=True)
        sils = [win0 + float(m) for m in re.findall(r"silence_start: (\d+\.?\d*)", r.stderr)]
        cand = [pv for pv in sils if (pv - delta) - start >= 16.0]
        if cand:
            pv = min(cand, key=lambda a: abs(a - center))
            return (pv - delta) - start + 0.30  # дать слову полностью договорить в паузу
    return end_dur(src, start, target)  # фолбэк: стык сцены


def make_short(src: Path, start: float, dur: float, cap_png: Path, out: Path):
    """Просто останавливается на моменте (стык сцены): 9:16 + подпись, БЕЗ фейда, звук до конца."""
    vfo = max(0.4, dur - 0.5)  # фейд-в-чёрный только на видео (голос НЕ приглушаем)
    vf = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=28:4,eq=brightness=-0.06[bg];"
          f"[0:v]scale={VID_W}:{VID_H}[fg];[bg][fg]overlay=0:{VID_Y}[base];"
          f"[base][1:v]overlay=0:0,fade=t=out:st={vfo:.2f}:d=0.5[out]")
    subprocess.run(["ffmpeg", "-y", "-ss", f"{start:.2f}", "-t", f"{dur:.2f}", "-i", str(src),
                    "-i", str(cap_png), "-filter_complex", vf, "-map", "[out]", "-map", "0:a",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-b:a", "192k",
                    str(out)], capture_output=True)
    return out.exists() and out.stat().st_size > 50000


def run_picks(picks, ti, ru_tc, en_tc) -> int:
    SHORTS.mkdir(parents=True, exist_ok=True)
    EN_PROJ = RU_PROJ.parent / "2026-08-25_aysberg-dreamworks-lost-media-i-temnaya-skrytaya-storona-stu_EN"
    align = {"ru": json.loads((RU_PROJ / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"],
             "en": json.loads((EN_PROJ / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]}
    scenes_full = json.loads((RU_PROJ / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    # 20 topic_announce-сцен по порядку = по одной на тему (topic_id у них None, берём по индексу)
    announces = [sc["id"] for sc in scenes_full if sc.get("section") == "topic_announce"]
    CTA = {"ru": "👉 Полный разбор — на канале @WebikStudio",
           "en": "👉 Full breakdown on the channel @Debik"}
    meta = {"ru": [], "en": []}
    for n, p in enumerate(picks, 1):
        idx = int(p["idx"]); target = max(30, min(52, float(p.get("dur", 45))))
        tid = ti[idx].get("id")
        for lang in ("ru", "en"):
            tc = (ru_tc if lang == "ru" else en_tc)
            if idx >= len(tc): continue
            start = max(0, tc[idx] + 0.2)                     # ровно с титра темы (без хвоста прошлой)
            dur = min(58, voice_pause_end(VOICE[lang], start, target, 0.0, SRC[lang]))  # голос синхронен mp4 → delta=0
            hook = p["hook_ru"] if lang == "ru" else p["hook_en"]
            cap = SHORTS / f"_cap_{lang}_{n:02d}.png"
            caption_png(hook, cap)
            out = SHORTS / f"short_{lang.upper()}_{n:02d}.mp4"
            ok = make_short(SRC[lang], start, dur, cap, out)
            cap.unlink(missing_ok=True)
            title = p["title_ru"] if lang == "ru" else p["title_en"]
            meta[lang].append(f"## {n:02d}. {title}\n{hook}\n{CTA[lang]}  ·  ~{int(dur)}s  ·  из {int(start//60)}:{int(start%60):02d}")
            print(f"  {'✓' if ok else '✗'} short_{lang.upper()}_{n:02d} [{hook[:30]}] {int(dur)}s", flush=True)
    (OUTDIR / "shorts_meta_RU.md").write_text("# Shorts RU (Webik)\n\n" + "\n\n".join(meta["ru"]), encoding="utf-8")
    (OUTDIR / "shorts_meta_EN.md").write_text("# Shorts EN (Debik)\n\n" + "\n\n".join(meta["en"]), encoding="utf-8")
    print(f"\nшортсы → {SHORTS} | мета → shorts_meta_RU/EN.md")
    return 0


def main() -> int:
    d = json.loads((RU_PROJ / "scenes.json").read_text(encoding="utf-8"))
    ti = d["topics_index"]
    ru_tc = sorted(json.loads((SCRATCH / "ru_v4_tc.json").read_text()))
    en_tc = sorted(json.loads((SCRATCH / "en_v4_tc.json").read_text()))
    picks_cache = RU_PROJ / "shorts_picks.json"
    if picks_cache.exists():
        picks = json.loads(picks_cache.read_text(encoding="utf-8"))
        print(f"[кэш] выбор шортсов: {len(picks)}")
        return run_picks(picks, ti, ru_tc, en_tc)
    llm = ClaudeService(model="anthropic/claude-sonnet-4.5")
    ask = ("Pick the 8 STRONGEST topics for YouTube Shorts (most shocking / clickable) from this list. "
           "For each return {\"idx\": topic index 0-based, \"dur\": 35-52 seconds, "
           "\"hook_ru\": very short punchy RU caption (<45 chars, uppercase, shocking), "
           "\"hook_en\": very short punchy EN caption (<45 chars, uppercase), "
           "\"title_ru\": short RU shorts title with #shorts, \"title_en\": short EN title with #shorts}. "
           "Return ONLY a JSON array of 8 objects, ordered by impact.\n\nTOPICS:\n"
           + "\n".join(f'{i}: {t["title"]}' for i, t in enumerate(ti)))
    picks = llm.call_json(ask, max_tokens=3000, temperature=0.5,
                          system="You are a viral YouTube Shorts editor for a dark documentary channel.")
    if isinstance(picks, dict):
        picks = picks.get("shorts") or picks.get("items") or []
    picks = picks[:8]
    picks_cache.write_text(json.dumps(picks, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"выбрано шортсов: {len(picks)}")
    return run_picks(picks, ti, ru_tc, en_tc)


if __name__ == "__main__":
    sys.exit(main())
