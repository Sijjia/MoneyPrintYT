"""Переделка Me and My Shadow (047-058) на РАЗНЫЕ источники (md5-дедуп, чтобы кадры не повторялись)
+ замена сцены 111 (тема Aardman×DreamWorks). Тело→V3, графика 047/053→V7. Новый префикс ms2_ (обход кэша bin)."""
import hashlib, json, os, shutil, subprocess, sys, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
PROJECT = ROOT / "projects" / "2026-08-25_aysberg-dreamworks-lost-media-i-temnaya-skrytaya-storona-stu"
REMOTION = ROOT / "remotion"; PUBV = REMOTION / "public" / "videos"
FIX = PROJECT / "assets" / "video_stock" / "_fixed"; GFX = PROJECT / "assets" / "graphics"; UNIQ = PROJECT / "assets" / "_uniq"
for d in (PUBV, FIX, GFX, UNIQ): d.mkdir(parents=True, exist_ok=True)
YT = [str(ROOT.parent / "webik-pipeline" / ".venv" / "Scripts" / "python.exe"), "-m", "yt_dlp",
      "--no-warnings", "--extractor-args", "youtube:player_client=android"]
PRPROJ = PROJECT / "project_template.prproj"
GRAPHIC = {"scene_047": "dossier", "scene_053": "terminated"}

# по сцене — свой запрос (визуально-разные источники, но по теме DreamWorks/анимация/студия)
MS_Q = {
    "scene_047": "Me and My Shadow DreamWorks test footage animation",
    "scene_048": "DreamWorks Animation 2010 movie lineup trailer",
    "scene_049": "hand drawn animation pencil test process",
    "scene_050": "CGI animation studio artists working b-roll",
    "scene_051": "DreamWorks Animation logo intro",
    "scene_052": "animation studio empty office layoffs",
    "scene_053": "abandoned film production concept art",
    "scene_054": "2D 3D hybrid animation short film",
    "scene_055": "animation storyboard sketch artist drawing",
    "scene_056": "old film reel projector archive footage",
    "scene_057": "DreamWorks Animation Glendale studio building",
    "scene_058": "classic hand drawn animation cels closeup",
}
SC111 = {"scene_111": "Flushed Away 2006 DreamWorks Aardman movie scene"}
SPARES = ["animation studio production pipeline b-roll", "stop motion animation studio", "film archive vault old reels",
          "movie studio backlot aerial", "cartoon animation drawing timelapse", "vintage cinema projector dark room"]


def md5(f):
    h = hashlib.md5()
    with open(f, "rb") as fh:
        for c in iter(lambda: fh.read(65536), b""): h.update(c)
    return h.hexdigest()


def dur(f):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                       capture_output=True, text=True)
    try: return float(r.stdout.strip())
    except: return 0


def dl(query, dst):
    r = subprocess.run(YT + ["--download-sections", "*5-20", "--force-keyframes-at-cuts",
                       "-o", str(dst), f"ytsearch1:{query}"], capture_output=True, text=True, timeout=200)
    return dst.exists() and dst.stat().st_size > 25000


def fetch_unique(sid, query, slot, tmp, seen):
    tries = [query] + SPARES
    for qi, q in enumerate(tries):
        raw = tmp / f"{sid}_{qi}.mp4"
        if not dl(q, raw): continue
        h = md5(raw)
        if h in seen: continue          # тот же ролик уже брали → следующий запрос
        seen.add(h)
        up = tmp / f"{sid}_u.mp4"
        subprocess.run(["ffmpeg", "-y", "-i", str(raw), "-vf", "scale=1920:1080:flags=lanczos,unsharp=5:5:0.4",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-an", str(up)], capture_output=True)
        out = FIX / f"ms2_{sid}.mp4"
        loop = ["-stream_loop", "-1"] if dur(up) < slot else []
        subprocess.run(["ffmpeg", "-y"] + loop + ["-i", str(up), "-t", f"{slot:.2f}",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-an", str(out)], capture_output=True)
        if out.exists() and out.stat().st_size > 25000:
            return out, q
    return None, None


def main() -> int:
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    tmp = Path(tempfile.mkdtemp()); seen = set(); got = {}
    targets = {**MS_Q, **SC111}
    for sid, q in targets.items():
        if sid not in al: continue
        slot = max(2.0, al[sid]["end"] - al[sid]["start"]) + 0.3
        out, used = fetch_unique(sid, q, slot, tmp, seen)
        if out: got[sid] = out; print(f"  ✓ {sid} ({dur(out):.1f}с) «{used[:40]}»", flush=True)
        else: print(f"  ✗ {sid}", flush=True)

    # перерендер график 047/053 с новым (уникальным) футажём
    for sid, treat in GRAPHIC.items():
        if sid not in got: continue
        shutil.copy(got[sid], PUBV / f"ms2_{sid}.mp4")
        slot = max(2.0, al[sid]["end"] - al[sid]["start"]) + 0.3; frames = max(60, round(slot * 30))
        props = {"videoSrc": f"videos/ms2_{sid}.mp4", "videoLoopFrames": max(30, round(dur(got[sid]) * 30)),
                 "caseNo": "АРХИВ · DREAMWORKS" if treat == "dossier" else "ПРОИЗВОДСТВО",
                 "title": "ME AND MY SHADOW", "subtitle": "ОТМЕНЁННЫЙ ГИБРИД 2D/3D" if treat == "dossier" else "",
                 "stamp": "ОТМЕНЁН" if treat == "dossier" else "ОСТАНОВЛЕНО",
                 "meta": [{"k": "АНОНС", "v": "2010"}, {"k": "СТАТУС", "v": "НЕ ВЫШЕЛ"}] if treat == "dossier" else [],
                 "accent": "#d9282f", "durationInFrames": frames}
        pf = REMOTION / f"_ms2_{sid}.json"; pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
        out = GFX / f"{sid}.mp4"
        subprocess.run(f'npx remotion render CancelledDossier "{os.path.relpath(out,REMOTION).replace(os.sep,"/")}" '
                       f'--props="{os.path.relpath(pf,REMOTION).replace(os.sep,"/")}" --codec=h264 --muted --log=error',
                       cwd=str(REMOTION), shell=True, capture_output=True, text=True)
        pf.unlink(missing_ok=True); print(f"  ✓ графика {sid} перерендерена", flush=True)

    # укладка: тело→V3, графика→V7 (уникальные имена ms2_/msg2_)
    import pymiere
    from pymiere.wrappers import time_from_seconds
    from services.premiere_template.timeline_ops import import_media
    seq = pymiere.objects.app.project.activeSequence; v3 = seq.videoTracks[2]; v7 = seq.videoTracks[6]
    def place(track, src, pref, sid):
        u = UNIQ / f"{pref}_{sid}.mp4"
        if not (u.exists() and u.stat().st_size == src.stat().st_size): shutil.copy(src, u)
        it = import_media(u)
        if it is None: return False
        track.overwriteClip(it, time_from_seconds(round(al[sid]["start"], 2))); return True
    pv = pg = 0
    for sid, f in got.items():
        if sid in GRAPHIC:
            g = GFX / f"{sid}.mp4"
            if g.exists() and place(v7, g, "msg2", sid): pg += 1
        else:
            if place(v3, f, "ms2", sid): pv += 1
    before = PRPROJ.stat().st_mtime
    pymiere.objects.app.project.save(); time.sleep(1.5)
    print(f"\nуложено: тело→V3 {pv}, графика→V7 {pg} | уникальных источников {len(seen)} | сейв {'✓' if PRPROJ.stat().st_mtime>before else '✗'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
