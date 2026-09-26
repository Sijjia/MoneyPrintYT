"""Шортсы (8 RU + 8 EN) «Айсберг Adult Swim» из готовых mp4: LLM выбирает 8 тем + хук-подписи,
режем сегмент с титра темы, 9:16 (размытый фон + вписка 16:9 + подпись сверху), конец = стоп на
паузе голоса (полное предложение), видео-фейд в чёрное, БЕЗ приглушения голоса. CTA в мете.
→ E:\\...\\Айсберг Adult Swim\\Shorts\\ + shorts_meta_RU/EN.md.
EN-канал: Deb1k @deb1kstuido."""
import json, subprocess, sys, textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.llm.claude import ClaudeService
from PIL import Image, ImageDraw, ImageFont

RU_PROJ = ROOT / "projects" / "2026-08-31_aysberg-adult-swim-temnaya-skrytaya-storona-nochnogo-bloka-c"
EN_PROJ = ROOT / "projects" / "2026-08-31_aysberg-adult-swim-temnaya-skrytaya-storona-nochnogo-bloka-c_EN"
OUTDIR = Path(r"E:\video for ytb\Webik\Айсберг Adult Swim")
SHORTS = OUTDIR / "Shorts"
SRC = {"ru": OUTDIR / "Айсберг Adult Swim_RU.mp4", "en": OUTDIR / "Айсберг Adult Swim_EN.mp4"}
VOICE = {"ru": RU_PROJ / "assets" / "voice" / "full.mp3", "en": EN_PROJ / "assets" / "voice" / "full.mp3"}
FONT = r"C:\Windows\Fonts\ariblk.ttf"
W, H = 1080, 1920
VID_W = 1080
VID_H = int(VID_W * 9 / 16)      # 608
VID_Y = (H - VID_H) // 2
CTA = {"ru": "👉 Полный разбор — на канале @WebikStudio",
       "en": "👉 Full breakdown on the channel @deb1kstuido"}


def topic_tc(proj: Path):
    """таймкоды 20 тем = старты карточек тем (topic_card) по порядку времени."""
    scenes = json.loads((proj / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    al = json.loads((proj / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    tcs = [al.get(s["id"], {}).get("start", 0) for s in scenes
           if (s.get("visual") or {}).get("type") == "topic_card"]
    return sorted(tcs)


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


def end_dur(src: Path, start: float, target: float) -> float:
    import re
    win0 = start + max(15.0, target - 8.0)
    r = subprocess.run(["ffmpeg", "-ss", f"{win0:.2f}", "-t", "16", "-i", str(src),
                        "-vf", "blackdetect=d=0.15:pix_th=0.06", "-an", "-f", "null", "-"],
                       capture_output=True, text=True)
    abss = [win0 + float(m) for m in re.findall(r"black_start:(\d+\.?\d*)", r.stderr)]
    cand = [a for a in abss if a - start >= 20.0]
    if cand:
        return min(cand, key=lambda a: abs(a - (start + target))) - start - 0.15
    return target


def voice_pause_end(voice: Path, start: float, target: float, delta: float, src: Path) -> float:
    """Конец на паузе голоса (полное предложение). delta = voice_time - mp4_time."""
    import re
    center = start + delta + target
    win0 = max(0.0, center - 16.0)
    for nz, dd in (("-40", "0.40"), ("-36", "0.30"), ("-32", "0.22"), ("-28", "0.18"), ("-24", "0.16"), ("-21", "0.16")):
        r = subprocess.run(["ffmpeg", "-ss", f"{win0:.2f}", "-t", "34", "-i", str(voice),
                            "-af", f"silencedetect=noise={nz}dB:d={dd}", "-f", "null", "-"],
                           capture_output=True, text=True)
        sils = [win0 + float(m) for m in re.findall(r"silence_start: (\d+\.?\d*)", r.stderr)]
        cand = [pv for pv in sils if (pv - delta) - start >= 16.0]
        if cand:
            pv = min(cand, key=lambda a: abs(a - center))
            return (pv - delta) - start + 0.30
    return end_dur(src, start, target)


def make_short(src: Path, start: float, dur: float, cap_png: Path, out: Path):
    vfo = max(0.4, dur - 0.5)
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
    meta = {"ru": [], "en": []}
    tcmap = {"ru": ru_tc, "en": en_tc}
    for n, p in enumerate(picks, 1):
        idx = int(p["idx"]); target = max(30, min(52, float(p.get("dur", 45))))
        for lang in ("ru", "en"):
            tc = tcmap[lang]
            if idx >= len(tc):
                continue
            start = max(0, tc[idx] + 0.2)
            dur = min(58, voice_pause_end(VOICE[lang], start, target, 0.0, SRC[lang]))
            hook = p["hook_ru"] if lang == "ru" else p["hook_en"]
            cap = SHORTS / f"_cap_{lang}_{n:02d}.png"
            caption_png(hook, cap)
            out = SHORTS / f"short_{lang.upper()}_{n:02d}.mp4"
            ok = make_short(SRC[lang], start, dur, cap, out)
            cap.unlink(missing_ok=True)
            title = p["title_ru"] if lang == "ru" else p["title_en"]
            meta[lang].append(f"## {n:02d}. {title}\n{hook}\n{CTA[lang]}  ·  ~{int(dur)}s  ·  из {int(start//60)}:{int(start%60):02d}")
            print(f"  {'✓' if ok else '✗'} short_{lang.upper()}_{n:02d} [{hook[:30]}] {int(dur)}s", flush=True)
    (OUTDIR / "shorts_meta_RU.md").write_text("# Shorts RU (Webik @WebikStudio)\n\n" + "\n\n".join(meta["ru"]), encoding="utf-8")
    (OUTDIR / "shorts_meta_EN.md").write_text("# Shorts EN (Deb1k @deb1kstuido)\n\n" + "\n\n".join(meta["en"]), encoding="utf-8")
    print(f"\nшортсы → {SHORTS} | мета → shorts_meta_RU/EN.md")
    return 0


def main() -> int:
    ti = json.loads((RU_PROJ / "scenes.json").read_text(encoding="utf-8"))["topics_index"]
    ru_tc = topic_tc(RU_PROJ)
    en_tc = topic_tc(EN_PROJ)
    print(f"тем: {len(ti)} | RU-тк: {len(ru_tc)} | EN-тк: {len(en_tc)}")
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
                          system="You are a viral YouTube Shorts editor for a dark documentary channel about Adult Swim.")
    if isinstance(picks, dict):
        picks = picks.get("shorts") or picks.get("items") or []
    picks = picks[:8]
    picks_cache.write_text(json.dumps(picks, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"выбрано шортсов: {len(picks)}")
    return run_picks(picks, ti, ru_tc, en_tc)


if __name__ == "__main__":
    sys.exit(main())
