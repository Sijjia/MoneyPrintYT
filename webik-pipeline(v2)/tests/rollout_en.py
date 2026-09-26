"""Раскатка графики DreamWorks по graphics_plan_v2_dw.json — с РАЗНООБРАЗИЕМ:
палитра-акцент по приёмам, варианты раскладки досье (monitor/fullbleed/sidebar), развод контент-дублей.
Ре-рендерит и кладёт на V7 уникальными именами (gfxd_)."""
import json, os, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
PROJECT = ROOT / "projects" / "2026-08-25_aysberg-dreamworks-lost-media-i-temnaya-skrytaya-storona-stu_EN"
REMOTION = ROOT / "remotion"; PUBV = REMOTION / "public" / "videos"
OUT = PROJECT / "assets" / "graphics"; UNIQ = PROJECT / "assets" / "_uniq"
PUBV.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True); UNIQ.mkdir(parents=True, exist_ok=True)
FOOTAGE = {"dossier", "cut_stamp", "terminated", "filmstrip", "drama_freeze", "uncanny", "split", "glitch"}
DOSSIER_FAM = {"dossier", "cut_stamp", "terminated"}

# палитра-акцент по приёмам (против «всё красное»)
PALETTE = {"dossier": "#d9282f", "cut_stamp": "#e8a33d", "terminated": "#b0202a", "filmstrip": "#38c7b8",
           "drama_freeze": "#d9532f", "uncanny": "#7fd14f", "glitch": "#ff3df0", "split": "#9b6cff",
           "money": "#d9282f", "headline": "#c9a24b", "timeline": "#4f9fd1", "quote": "#e0b445"}
# развод контент-дублей: 2-й B.O.O.-досье → глитч; 2-й «Принц Египта»-filmstrip → drama_freeze
REASSIGN = {"scene_196": "glitch", "scene_211": "drama_freeze"}
VARIANTS = ["monitor", "fullbleed", "sidebar"]


def dur(f):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                       capture_output=True, text=True)
    try: return float(r.stdout.strip())
    except: return 0


def clip_of(sid, man):
    # EN: футаж берём из EN/_trimmed (создан assemble_en, уже нужной длины и с фиксами через манифест)
    t = PROJECT / "assets" / "video_stock" / "_trimmed" / f"{sid}.mp4"
    if t.exists(): return t
    # фолбэк: фикс-файлы в RU-папке (шаринг)
    base = os.path.basename((man.get(sid, {}) or {}).get("path", ""))
    if base and Path(base).suffix == ".mp4":
        p = Path((man.get(sid, {}) or {}).get("path", ""))
        if p.exists(): return p
    return None


def image_of(sid, man):
    p = (man.get(sid, {}) or {}).get("path", "")
    return Path(p) if p and Path(p).exists() and Path(p).suffix.lower() in (".jpg", ".jpeg", ".png") else None


def money_fields(v, accent):
    num = re.sub(r"\D", "", str(v.get("number", ""))) or "0"
    raw = f"{v.get('number','')} {v.get('label','')} {v.get('sub','')}".lower()
    prefix = "−$" if "$" in raw or "loss" in raw or "flop" in raw or "fail" in raw else ""
    suffix = " M" if ("million" in raw or "$" in raw) else (" PEOPLE" if ("layoff" in raw or "employee" in raw or "staff" in raw) else "")
    neg = ("$" in raw or "loss" in raw or "flop" in raw or "fail" in raw)
    return {"number": num, "prefix": prefix, "suffix": suffix,
            "label": (v.get("label") or v.get("title") or "").upper()[:26], "sub": (v.get("sub") or "")[:40],
            "negative": neg, "accent": accent}


def comp_props(sid, v, man, frames, variant):
    t = v.get("treatment"); acc = PALETTE.get(t, "#d9282f"); vsrc = ""; imgsrc = ""; lf = 150
    if t in FOOTAGE:
        c = clip_of(sid, man)
        if c:
            shutil.copy(c, PUBV / f"{sid}.mp4"); vsrc = f"videos/{sid}.mp4"; lf = max(30, round(dur(c) * 30))
        elif t in DOSSIER_FAM:
            im = image_of(sid, man)
            if not im: return None, None
            (REMOTION / "public" / "dwimg").mkdir(parents=True, exist_ok=True)
            shutil.copy(im, REMOTION / "public" / "dwimg" / f"{sid}.jpg"); imgsrc = f"dwimg/{sid}.jpg"
        else:
            return None, None
    base = {"durationInFrames": frames}
    if t == "dossier":
        return "CancelledDossier", {**base, "variant": variant, "videoSrc": vsrc, "imageSrc": imgsrc, "videoLoopFrames": lf,
            "caseNo": "ARCHIVE · DREAMWORKS", "title": (v.get("title") or "")[:26], "subtitle": (v.get("subtitle") or "")[:44],
            "stamp": v.get("stamp") or "LOST", "meta": (v.get("meta") or [])[:3], "accent": acc}
    if t == "cut_stamp":
        return "CancelledDossier", {**base, "variant": variant, "videoSrc": vsrc, "imageSrc": imgsrc, "videoLoopFrames": lf,
            "caseNo": "DELETED SCENE", "title": (v.get("title") or "")[:26], "subtitle": "",
            "stamp": v.get("stamp") or "CUT", "meta": [], "accent": acc}
    if t == "terminated":
        return "CancelledDossier", {**base, "variant": variant, "videoSrc": vsrc, "imageSrc": imgsrc, "videoLoopFrames": lf,
            "caseNo": "PRODUCTION", "title": (v.get("title") or "")[:26], "subtitle": (v.get("subtitle") or "")[:44],
            "stamp": "SHUT DOWN", "meta": [], "accent": acc}
    if t == "filmstrip":
        return "FilmStrip", {**base, "videoSrc": vsrc, "videoLoopFrames": lf,
            "title": (v.get("title") or "")[:26], "subtitle": (v.get("subtitle") or "")[:40], "accent": acc}
    if t == "drama_freeze":
        return "DramaFreeze", {**base, "videoSrc": vsrc, "videoLoopFrames": lf,
            "title": (v.get("title") or "")[:28], "subtitle": (v.get("subtitle") or "")[:40], "accent": acc}
    if t == "uncanny":
        return "UncannyCGI", {**base, "videoSrc": vsrc, "videoLoopFrames": lf,
            "title": (v.get("title") or "UNCANNY VALLEY")[:26], "subtitle": (v.get("subtitle") or "")[:40], "accent": acc}
    if t == "glitch":
        return "GlitchLeak", {**base, "videoSrc": vsrc, "videoLoopFrames": lf,
            "title": (v.get("title") or "LEAK")[:20], "subtitle": (v.get("subtitle") or "CORRUPTED FOOTAGE")[:34], "accent": acc}
    if t == "split":
        a = v.get("a") or {}; b = v.get("b") or {}
        return "SplitCompare", {**base, "videoSrc": vsrc, "videoLoopFrames": lf, "title": (v.get("title") or "COMPARISON")[:24],
            "aLabel": (a.get("label") or "BEFORE")[:18], "aSub": (a.get("sub") or "")[:22],
            "bLabel": (b.get("label") or "AFTER")[:18], "bSub": (b.get("sub") or "")[:22], "accent": acc}
    if t == "money":
        return "MoneyCounter", {**base, **money_fields(v, acc)}
    if t == "headline":
        return "NewsHeadline", {**base, "headline": (v.get("headline") or v.get("title") or "")[:60],
            "source": (v.get("source") or "THE HOLLYWOOD REPORTER")[:30], "date": str(v.get("date") or ""), "accent": acc}
    if t == "quote":
        return "QuoteCardDW", {**base, "text": (v.get("text") or "")[:120], "author": (v.get("author") or "")[:40], "accent": acc}
    if t == "timeline":
        return "StudioTimeline", {**base, "title": (v.get("title") or "TIMELINE")[:24],
            "events": [{"year": str(e.get("year", "")), "text": (e.get("text") or "").upper()[:26]} for e in (v.get("events") or [])[:4]], "accent": acc}
    return None, None


def main() -> int:
    plan = json.loads((PROJECT / "graphics_plan_v2_dw.json").read_text(encoding="utf-8"))
    man = json.loads((PROJECT / "assets" / "images" / "manifest.json").read_text(encoding="utf-8"))
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    # применяем развод дублей
    for sid, t in REASSIGN.items():
        if sid in plan: plan[sid]["treatment"] = t
    items = sorted([(sid, v) for sid, v in plan.items() if sid in al], key=lambda kv: al[kv[0]]["start"])
    # варианты раскладки по досье-семейству (round-robin по времени → соседи разные)
    dossier_scenes = [sid for sid, v in items if v.get("treatment") in DOSSIER_FAM]
    variant_of = {sid: VARIANTS[i % 3] for i, sid in enumerate(dossier_scenes)}
    print(f"моментов: {len(items)} | досье-раскладки: " +
          ", ".join(f"{s.split('_')[1]}:{variant_of[s]}" for s in dossier_scenes))

    rendered = {}
    for sid, v in items:
        a = al[sid]; slot = max(2.0, a["end"] - a["start"]) + 0.3; frames = max(60, round(slot * 30))
        comp, props = comp_props(sid, v, man, frames, variant_of.get(sid, "monitor"))
        if not comp: print(f"  ✗ {sid} [{v.get('treatment')}]: нет компонента/клипа"); continue
        pf = REMOTION / f"_gv_{sid}.json"; pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
        outp = OUT / f"{sid}.mp4"
        subprocess.run(f'npx remotion render {comp} "{os.path.relpath(outp,REMOTION).replace(os.sep,"/")}" '
                       f'--props="{os.path.relpath(pf,REMOTION).replace(os.sep,"/")}" --codec=h264 --muted --log=error',
                       cwd=str(REMOTION), shell=True, capture_output=True, text=True)
        pf.unlink(missing_ok=True)
        if outp.exists() and outp.stat().st_size > 20000:
            rendered[sid] = outp
            extra = f" [{variant_of[sid]}]" if sid in variant_of else ""
            print(f"  ✓ {sid} [{v.get('treatment')}] {comp}{extra}", flush=True)
        else:
            print(f"  ✗ {sid} [{v.get('treatment')}] рендер упал", flush=True)
    print(f"отрендерено: {len(rendered)}/{len(items)}")

    # укладка на V7 уникальными именами (gfxd_), чистим V7
    import pymiere
    from pymiere.wrappers import time_from_seconds
    from services.premiere_template.timeline_ops import import_media
    seq = pymiere.objects.app.project.activeSequence; v7 = seq.videoTracks[6]
    for cl in reversed(list(v7.clips)):
        try: cl.remove(False, False)
        except Exception: pass
    print(f"V7 очищен → {v7.clips.numItems}", flush=True)
    placed = 0
    for sid, outp in sorted(rendered.items(), key=lambda kv: al[kv[0]]["start"]):
        u = UNIQ / f"gfxd_{sid}.mp4"
        if not (u.exists() and u.stat().st_size == outp.stat().st_size): shutil.copy(outp, u)
        it = import_media(u)
        if it is None: continue
        v7.overwriteClip(it, time_from_seconds(round(al[sid]["start"], 2))); placed += 1
    PRPROJ = PROJECT / "project_template.prproj"; before = PRPROJ.stat().st_mtime
    pymiere.objects.app.project.save()
    import time; time.sleep(2.0)
    try: mp = v7.clips[0].projectItem.getMediaPath()
    except Exception: mp = "?"
    print(f"\nграфика→V7: {placed}/{len(rendered)} | V7[0]=...{mp[-30:]} | сейв {'✓' if PRPROJ.stat().st_mtime>before else '✗'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
