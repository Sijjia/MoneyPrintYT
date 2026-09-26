"""Раскатка графики DreamWorks: по graphics_plan_dw.json оборачивает футаж «dossier»-сцен
в CancelledDossier (архив-дизайн со штампом/без) и кладёт на V3. keep-сцены не трогает.
Фаза 1 рендер (без Premiere) → Фаза 2 укладка (pymiere)."""
import json, os, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
PROJECT = ROOT / "projects" / "2026-08-25_aysberg-dreamworks-lost-media-i-temnaya-skrytaya-storona-stu"
REMOTION = ROOT / "remotion"
PUBV = REMOTION / "public" / "videos"
OUT = PROJECT / "assets" / "graphics"
PUBV.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)


def dur(f):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                       capture_output=True, text=True)
    try: return float(r.stdout.strip())
    except: return 0


def src_clip(sid, v):
    """Актуальный клип сцены: _fixed > _slow > video_stock."""
    base = os.path.basename(v.get("path", ""))
    for sub in ("_fixed", "_slow", ""):
        p = PROJECT / "assets" / "video_stock" / sub / base if sub else PROJECT / "assets" / "video_stock" / base
        if p.exists(): return p
    return None


def main() -> int:
    plan = json.loads((PROJECT / "graphics_plan_dw.json").read_text(encoding="utf-8"))
    man = json.loads((PROJECT / "assets" / "images" / "manifest.json").read_text(encoding="utf-8"))
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    doss = [(sid, p) for sid, p in plan.items() if p.get("treatment") == "dossier" and sid in al]
    print(f"dossier-сцен: {len(doss)}")

    # ── Фаза 1: рендер ──
    rendered = {}
    for k, (sid, p) in enumerate(doss):
        outp = OUT / f"{sid}.mp4"
        a = al[sid]; slot = max(2.0, a["end"] - a["start"]) + 0.3; frames = max(60, round(slot * 30))
        if outp.exists() and abs(dur(outp) - slot) < 0.6:
            rendered[sid] = outp; continue
        clip = src_clip(sid, man.get(sid, {}))
        if not clip: print(f"  ✗ {sid}: нет клипа"); continue
        pub = PUBV / f"{sid}.mp4"; shutil.copy(clip, pub)
        cd = dur(clip)
        props = {
            "videoSrc": f"videos/{sid}.mp4",
            "videoLoopFrames": max(30, round(cd * 30)),
            "caseNo": "АРХИВ · DREAMWORKS",
            "title": (p.get("title") or "")[:26],
            "subtitle": (p.get("subtitle") or "")[:44],
            "stamp": p.get("stamp") or "",
            "meta": (p.get("meta") or [])[:3],
            "accent": "#d9282f",
            "durationInFrames": frames,
        }
        pf = REMOTION / f"_gp_{sid}.json"; pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
        rel_out = os.path.relpath(outp, REMOTION).replace(os.sep, "/")
        rel_pf = os.path.relpath(pf, REMOTION).replace(os.sep, "/")
        subprocess.run(f'npx remotion render CancelledDossier "{rel_out}" --props="{rel_pf}" '
                       f'--codec=h264 --muted --log=error', cwd=str(REMOTION), shell=True, capture_output=True, text=True)
        pf.unlink(missing_ok=True)
        if outp.exists() and outp.stat().st_size > 20000:
            rendered[sid] = outp
            if len(rendered) % 5 == 0: print(f"  ...рендер {len(rendered)}/{len(doss)}", flush=True)
        else:
            print(f"  ✗ {sid}: рендер упал", flush=True)
    print(f"отрендерено: {len(rendered)}/{len(doss)}")

    # ── Фаза 2: укладка на V3 ──
    import pymiere
    from pymiere.wrappers import time_from_seconds
    from services.premiere_template.timeline_ops import import_media
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[2]
    placed = 0
    for sid, outp in sorted(rendered.items(), key=lambda kv: al[kv[0]]["start"]):
        try:
            it = import_media(outp)
            if it is None: continue
            v3.overwriteClip(it, time_from_seconds(round(al[sid]["start"], 2)))
            placed += 1
            if placed % 10 == 0: print(f"  ...уложено {placed}", flush=True)
        except Exception as e:
            print(f"  ✗ place {sid}: {str(e)[:50]}")
    pymiere.objects.app.project.save()
    print(f"\nграфика уложена на V3: {placed}/{len(rendered)}; проект сохранён")
    return 0


if __name__ == "__main__":
    sys.exit(main())
