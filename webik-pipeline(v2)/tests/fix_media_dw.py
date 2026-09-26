"""Точечный фикс медиа DreamWorks: B.O.O. (мем Bee Movie вместо футажа) + луп-сцены.
yt-dlp (android+POT) → апскейл 1080p → залупка/трим ровно под слот сцены → укладка на V3."""
import json, os, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
PROJECT = ROOT / "projects" / "2026-08-25_aysberg-dreamworks-lost-media-i-temnaya-skrytaya-storona-stu"
VID = PROJECT / "assets" / "video_stock"
FIXDIR = VID / "_fixed"
FIXDIR.mkdir(parents=True, exist_ok=True)
YTDLP = [str(ROOT.parent / "webik-pipeline" / ".venv" / "Scripts" / "python.exe"), "-m", "yt_dlp"]
YT = ["--no-warnings", "--extractor-args", "youtube:player_client=android"]

# sid -> query. B.O.O. один запрос, офсет варьируем по индексу.
TARGETS = {}
for i, sid in enumerate([f"scene_{n}" for n in range(192, 201)]):
    TARGETS[sid] = ("DreamWorks Bureau of Otherworldly Operations BOO cancelled movie", i)
TARGETS["scene_065"] = ("Madagascar 2005 Alex hallucinates friends as steaks scene", 0)
TARGETS["scene_144"] = ("Kung Fu Panda 2 Po sad flashback scene", 0)


def dur(f):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                       capture_output=True, text=True)
    try: return float(r.stdout.strip())
    except: return 0


def build(sid, query, idx, slot, tmp):
    start = 6 + idx * 12
    raw = tmp / f"{sid}_raw.mp4"
    subprocess.run(YTDLP + YT + ["--download-sections", f"*{start}-{start+14}", "--force-keyframes-at-cuts",
                   "-o", str(raw), f"ytsearch1:{query}"], capture_output=True, text=True, timeout=180)
    if not raw.exists() or raw.stat().st_size < 20000:
        subprocess.run(YTDLP + YT + ["--download-sections", "*3-17", "--force-keyframes-at-cuts",
                       "-o", str(raw), f"ytsearch1:{query}"], capture_output=True, text=True, timeout=180)
    if not raw.exists() or raw.stat().st_size < 20000:
        return None
    up = tmp / f"{sid}_up.mp4"
    subprocess.run(["ffmpeg", "-y", "-i", str(raw), "-vf",
                    "scale=1920:1080:flags=lanczos,unsharp=5:5:0.5:5:5:0.0",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-an", str(up)],
                   capture_output=True, text=True)
    if not up.exists(): return None
    # залупка/трим ровно под слот
    out = FIXDIR / f"{sid}.mp4"
    subprocess.run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(up), "-t", f"{slot:.2f}",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-an", str(out)],
                   capture_output=True, text=True)
    return out if out.exists() and out.stat().st_size > 20000 else None


def main() -> int:
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    tmp = Path(tempfile.mkdtemp())
    built = {}
    for sid, (q, idx) in TARGETS.items():
        if sid not in al: continue
        slot = max(2.0, al[sid]["end"] - al[sid]["start"]) + 0.3
        outp = FIXDIR / f"{sid}.mp4"
        if outp.exists() and abs(dur(outp) - slot) < 0.5:
            built[sid] = outp; print(f"  кэш {sid}"); continue
        r = build(sid, q, idx, slot, tmp)
        if r: built[sid] = r; print(f"  ✓ {sid} ({dur(r):.1f}с) «{q[:34]}»", flush=True)
        else: print(f"  ✗ {sid} не скачалось", flush=True)
    print(f"собрано: {len(built)}/{len(TARGETS)}")

    # укладка на V3 (overwrite по времени сцены)
    import pymiere
    from pymiere.wrappers import time_from_seconds
    from services.premiere_template.timeline_ops import import_media
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[2]
    placed = 0
    for sid, outp in sorted(built.items(), key=lambda kv: al[kv[0]]["start"]):
        try:
            it = import_media(outp)
            if it is None: print(f"  ✗ import {sid}"); continue
            v3.overwriteClip(it, time_from_seconds(round(al[sid]["start"], 2)))
            placed += 1; print(f"  ✓V3 {sid}", flush=True)
        except Exception as e:
            print(f"  ✗ place {sid}: {str(e)[:50]}")
    pymiere.objects.app.project.save()
    print(f"\nуложено фиксов на V3: {placed}/{len(built)}; проект сохранён")
    return 0


if __name__ == "__main__":
    sys.exit(main())
