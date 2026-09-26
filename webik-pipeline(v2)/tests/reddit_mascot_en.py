"""Маскот МНОГО и точечно для «Айсберг Reddit»: авто-выбор футаж-сцен по всему таймлайну (разбить
монотонность), LLM даёт короткую подпись-реакцию, липсинк по голосу сцены + компаньон-кадр, кладёт на V3.
Аутро остаётся отдельным (MascotOutro). Premiere с проектом открыт.
  MASCOT_EVERY=70 ../webik-pipeline/.venv/Scripts/python.exe tests/reddit_mascot.py"""
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
import tests.mascot_demo as md
from services.llm.claude import ClaudeService
from services.premiere_template.timeline_ops import import_media, place_clip

PROJECT = ROOT / "projects" / "2026-09-13_aysberg-reddit-strannaya-i-trevozhnaya-storona_EN"
REMOTION = ROOT / "remotion"
GFX = PROJECT / "assets" / "gfx"; GFX.mkdir(parents=True, exist_ok=True)
VOICE = PROJECT / "assets" / "voice" / "full.mp3"
V3 = 2
FPS = 30
EVERY = float(os.environ.get("MASCOT_EVERY", "72"))   # цель: ~1 маскот на N секунд
MINDUR = 3.0                                            # слот не короче
ACCENT = "#8a5cff"

SYS = ("You write SHORT host lines for a capybara mascot (the presenter) in a documentary about Reddit's "
       "dark side. For each scene's narration give ONE lively reaction line in the host's voice "
       "(conversational US English, no cheese, no cliches, 4-9 words) that heightens the moment. "
       "Do not invent facts beyond the narration.")
RULE = 'Return ONLY JSON [{"id","caption"}]. caption — a short lively English phrase (4-9 words).'


def clip_starts():
    csv = pymiere.core.eval_script(
        "(function(){var t=app.project.activeSequence.videoTracks[%d],a=[];"
        "for(var i=0;i<t.clips.numItems;i++)a.push(t.clips[i].start.seconds);return a.join(',');})()" % V3)
    return [float(x) for x in csv.split(",") if x.strip()]


def render(props, out, frames):
    props = dict(props); props["durationInFrames"] = frames
    pf = REMOTION / f"_msc_{out.stem}.json"; pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    subprocess.run(f'npx remotion render Mascot "{os.path.relpath(out, REMOTION).replace(os.sep,"/")}" '
                   f'--props="{os.path.relpath(pf, REMOTION).replace(os.sep,"/")}" --codec=h264 --muted --log=error',
                   cwd=str(REMOTION), shell=True, capture_output=True, text=True)
    pf.unlink(missing_ok=True)
    return out.exists() and out.stat().st_size > 20000


def main() -> int:
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    man = json.loads((PROJECT / "assets" / "images" / "manifest.json").read_text(encoding="utf-8"))
    trimmed = PROJECT / "assets" / "video_stock" / "_trimmed"
    CARD = {"level_card", "topic_card"}
    sc = {s["id"]: s for s in scenes}

    srt = sorted([(al[s["id"]]["start"], s["id"]) for s in scenes if s["id"] in al])
    dur = {}
    for i, (st, sid) in enumerate(srt):
        dur[sid] = (srt[i + 1][0] if i + 1 < len(srt) else st + 4) - st

    # кандидаты: обычный ФУТАЖ (не графика/фото/карточки/аутро), длинные слоты
    FOOT = {"pexels-video", "qcfix-hd", "parallax", "youtube-auto"}
    cand = []
    for st, sid in srt:
        s = sc[sid]
        if (s.get("visual") or {}).get("type") in CARD: continue
        if (s.get("section") or "") in ("outro", "cta", "conclusion"): continue
        if man.get(sid, {}).get("source") not in FOOT: continue
        if dur.get(sid, 0) < MINDUR: continue
        cand.append((st, sid))

    # распределяем ~1 на EVERY секунд
    picks, last = [], -1e9
    for st, sid in cand:
        if st - last >= EVERY:
            picks.append(sid); last = st
    print(f"футаж-кандидатов: {len(cand)} → маскот-вставок: {len(picks)}", flush=True)

    # LLM подписи
    llm = ClaudeService(model="anthropic/claude-sonnet-4.5")
    caps = {}
    for i in range(0, len(picks), 20):
        chunk = picks[i:i+20]
        lines = [f'{{"id":"{s}","vo":"{(sc[s].get("voiceover") or "").replace(chr(34)," ")[:180]}"}}' for s in chunk]
        try:
            res = llm.call_json(RULE + "\n\nСЦЕНЫ:\n" + "\n".join(lines), max_tokens=2500, temperature=0.5, system=SYS)
            if isinstance(res, dict): res = res.get("items") or []
            for r in res:
                if r.get("id"): caps[r["id"]] = (r.get("caption") or "").strip()
        except Exception as e:
            print(f"  LLM подписи батч упал: {str(e)[:50]}")

    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[V3]
    starts = clip_starts()
    def snap(t):
        """Ближайший РЕАЛЬНЫЙ старт клипа на V3 (не alignment) — чтоб маскот перекрыл сцену
        без огрызка-мелькания на стыке."""
        best, bs = 1e9, None
        for s in starts:
            if abs(s - t) < best: best, bs = abs(s - t), s
        return bs if best < 1.2 else None

    done = 0
    for k, sid in enumerate(picks):
        d = min(dur.get(sid, 4.0), 6.5)   # маскот не длиннее ~6.5с, чтоб не забивал
        t0 = snap(al[sid]["start"])       # снап на фактический старт клипа
        if t0 is None:
            continue
        seg = GFX / f"seg_msc_{sid}.wav"
        subprocess.run(["ffmpeg", "-y", "-ss", f"{t0:.2f}", "-t", f"{d:.2f}", "-i", str(VOICE),
                        "-ac", "1", "-ar", "22050", str(seg)], capture_output=True)
        mouth = md.mouth_track(seg, d + 0.2, FPS)
        # компаньон: приоритет — РЕАЛЬНОЕ фото этой/соседней сцены темы (на-тему, чётко), иначе кадр футажа
        comp = []
        cf = REMOTION / "public" / "mascot" / f"rd_{sid}.jpg"
        real_dir = REMOTION / "public" / "real"
        order = [s for _, s in srt]
        idx = order.index(sid) if sid in order else -1
        picked_real = None
        if idx >= 0:
            for off in [0, -1, 1, -2, 2, -3, 3, -4, 4, 5, 6]:   # ближайшее реальное фото темы
                j = idx + off
                if 0 <= j < len(order) and (real_dir / f"{order[j]}.jpg").exists():
                    picked_real = order[j]; break
        have_img = False
        if picked_real:
            import shutil as _sh
            _sh.copy2(real_dir / f"{picked_real}.jpg", cf); have_img = True
        else:
            eco = trimmed / f"{sid}.mp4"
            if eco.exists() and md.grab_frame(eco, cf):
                have_img = True
        # ФОРМАТЫ маскота (чтоб не однотипно): каждый 4-й — крупно по центру без картинки;
        # остальные — слева + картинка справа, но ОПУЩЕНА ниже (не липнет к верху).
        fmt = k % 4
        props = {"mouth": mouth, "jitter": 0.8, "caption": caps.get(sid, ""), "accent": ACCENT}
        if fmt == 3 or not have_img:
            props.update({"position": "center", "scale": 1.05})     # соло по центру
        else:
            yy = 0.50 if fmt == 1 else 0.46                          # НИЖЕ, чуть варьируем
            props.update({"position": "left", "scale": 0.9,
                          "companions": [{"src": f"mascot/rd_{sid}.jpg", "x": 0.71, "y": yy, "w": 700,
                                          "from": 8, "to": len(mouth) - 6}]})
        out = GFX / f"mascot_{sid}.mp4"
        if render(props, out, len(mouth)):
            item = import_media(out)
            if item is not None:
                place_clip(v3, item, t0); done += 1
                if done % 4 == 0: print(f"  ...уложено {done}", flush=True)
    pymiere.objects.app.project.save()
    print(f"\nмаскот-вставок уложено: {done}; сохранено", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
