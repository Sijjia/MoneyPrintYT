"""Фикс темы Me and My Shadow: Wikimedia отдал мусор → перекачиваю как реальный yt-dlp-футаж,
перерендериваю 2 графики темы (dossier/terminated) с новым футажём, укладываю (тело→V3, графика→V7)."""
import json, os, shutil, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
PROJECT = ROOT / "projects" / "2026-08-25_aysberg-dreamworks-lost-media-i-temnaya-skrytaya-storona-stu"
REMOTION = ROOT / "remotion"; PUBV = REMOTION / "public" / "videos"
FIX = PROJECT / "assets" / "video_stock" / "_fixed"
GFX = PROJECT / "assets" / "graphics"; UNIQ = PROJECT / "assets" / "_uniq"
for d in (PUBV, FIX, GFX, UNIQ): d.mkdir(parents=True, exist_ok=True)
YT = [str(ROOT.parent / "webik-pipeline" / ".venv" / "Scripts" / "python.exe"), "-m", "yt_dlp",
      "--no-warnings", "--extractor-args", "youtube:player_client=android"]
PRPROJ = PROJECT / "project_template.prproj"
Q = "Me and My Shadow DreamWorks cancelled movie test animation"
GRAPHIC = {"scene_047": ("dossier", "ОТМЕНЁН"), "scene_053": ("terminated", "ОСТАНОВЛЕНО")}
SCENES = [f"scene_{n:03d}" for n in range(47, 59)]  # 047-058


def dur(f):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                       capture_output=True, text=True)
    try: return float(r.stdout.strip())
    except: return 0


def fetch(sid, idx, slot, tmp):
    start = 8 + idx * 9
    raw = tmp / f"{sid}.mp4"
    subprocess.run(YT + ["--download-sections", f"*{start}-{start+13}", "--force-keyframes-at-cuts",
                   "-o", str(raw), f"ytsearch1:{Q}"], capture_output=True, text=True, timeout=180)
    if not raw.exists() or raw.stat().st_size < 20000:
        subprocess.run(YT + ["--download-sections", "*4-17", "--force-keyframes-at-cuts",
                       "-o", str(raw), f"ytsearch1:{Q}"], capture_output=True, text=True, timeout=180)
    if not raw.exists() or raw.stat().st_size < 20000: return None
    up = tmp / f"{sid}_u.mp4"
    subprocess.run(["ffmpeg", "-y", "-i", str(raw), "-vf", "scale=1920:1080:flags=lanczos,unsharp=5:5:0.5",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-an", str(up)], capture_output=True)
    out = FIX / f"{sid}.mp4"
    subprocess.run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(up), "-t", f"{slot:.2f}",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-an", str(out)], capture_output=True)
    return out if out.exists() and out.stat().st_size > 20000 else None


def main() -> int:
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    man = json.loads((PROJECT / "assets" / "images" / "manifest.json").read_text(encoding="utf-8"))
    import tempfile; tmp = Path(tempfile.mkdtemp())
    # Фаза A: футаж
    got = {}
    for i, sid in enumerate(SCENES):
        if sid not in al: continue
        if man.get(sid, {}).get("kind") == "video" and sid not in GRAPHIC:  # 049 уже видео
            pass
        slot = max(2.0, al[sid]["end"] - al[sid]["start"]) + 0.3
        r = fetch(sid, i, slot, tmp)
        if r: got[sid] = r; print(f"  ✓ футаж {sid} ({dur(r):.1f}с)", flush=True)
        else: print(f"  ✗ {sid}", flush=True)
    # Фаза B: перерендер график 047/053 с новым футажём
    for sid, (treat, stamp) in GRAPHIC.items():
        if sid not in got: continue
        shutil.copy(got[sid], PUBV / f"ms_{sid}.mp4")
        slot = max(2.0, al[sid]["end"] - al[sid]["start"]) + 0.3; frames = max(60, round(slot * 30))
        props = {"videoSrc": f"videos/ms_{sid}.mp4", "videoLoopFrames": max(30, round(dur(got[sid]) * 30)),
                 "caseNo": "АРХИВ · DREAMWORKS" if treat == "dossier" else "ПРОИЗВОДСТВО",
                 "title": "ME AND MY SHADOW", "subtitle": "ОТМЕНЁННЫЙ ГИБРИД 2D/3D" if treat == "dossier" else "",
                 "stamp": stamp, "meta": [{"k": "АНОНС", "v": "2010"}, {"k": "СТАТУС", "v": "НЕ ВЫШЕЛ"}] if treat == "dossier" else [],
                 "accent": "#d9282f", "durationInFrames": frames}
        pf = REMOTION / f"_ms_{sid}.json"; pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
        out = GFX / f"{sid}.mp4"
        subprocess.run(f'npx remotion render CancelledDossier "{os.path.relpath(out,REMOTION).replace(os.sep,"/")}" '
                       f'--props="{os.path.relpath(pf,REMOTION).replace(os.sep,"/")}" --codec=h264 --muted --log=error',
                       cwd=str(REMOTION), shell=True, capture_output=True, text=True)
        pf.unlink(missing_ok=True)
        print(f"  ✓ графика {sid} перерендерена", flush=True)
    # Фаза C: укладка
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
            if g.exists() and place(v7, g, "msgfx", sid): pg += 1
        else:
            if place(v3, f, "ms", sid): pv += 1
    before = PRPROJ.stat().st_mtime
    pymiere.objects.app.project.save(); time.sleep(1.5)
    print(f"\nуложено: тело→V3 {pv}, графика→V7 {pg} | сейв {'✓' if PRPROJ.stat().st_mtime>before else '✗'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
