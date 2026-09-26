"""Фикс логотип-сцен DreamWorks (019/024/025 — мусорные картинки с «Shrek»/буквами) →
реальный логотип-интро (мальчик с удочкой на луне), разные клипы + md5-дедуп. Тело→V3, префикс dwlogo_."""
import hashlib, json, os, shutil, subprocess, sys, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
PROJECT = ROOT / "projects" / "2026-08-25_aysberg-dreamworks-lost-media-i-temnaya-skrytaya-storona-stu"
FIX = PROJECT / "assets" / "video_stock" / "_fixed"; UNIQ = PROJECT / "assets" / "_uniq"
for d in (FIX, UNIQ): d.mkdir(parents=True, exist_ok=True)
YT = [str(ROOT.parent / "webik-pipeline" / ".venv" / "Scripts" / "python.exe"), "-m", "yt_dlp",
      "--no-warnings", "--extractor-args", "youtube:player_client=android"]
PRPROJ = PROJECT / "project_template.prproj"
Q = {"scene_019": "DreamWorks Animation logo intro boy fishing moon HD",
     "scene_024": "DreamWorks SKG logo history evolution all variants",
     "scene_025": "DreamWorks Animation opening logo compilation"}
SPARES = ["DreamWorks Animation logo 2016 clouds", "DreamWorks pictures intro logo",
          "DreamWorks Animation ident logo full", "classic DreamWorks logo moon boy"]


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


def fetch(sid, query, slot, tmp, seen):
    for qi, q in enumerate([query] + SPARES):
        raw = tmp / f"{sid}_{qi}.mp4"
        subprocess.run(YT + ["--download-sections", "*2-16", "--force-keyframes-at-cuts",
                       "-o", str(raw), f"ytsearch1:{q}"], capture_output=True, text=True, timeout=200)
        if not raw.exists() or raw.stat().st_size < 25000: continue
        h = md5(raw)
        if h in seen: continue
        seen.add(h)
        up = tmp / f"{sid}_u.mp4"
        subprocess.run(["ffmpeg", "-y", "-i", str(raw), "-vf", "scale=1920:1080:flags=lanczos,unsharp=5:5:0.4",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-an", str(up)], capture_output=True)
        out = FIX / f"dwlogo_{sid}.mp4"
        loop = ["-stream_loop", "-1"] if dur(up) < slot else []
        subprocess.run(["ffmpeg", "-y"] + loop + ["-i", str(up), "-t", f"{slot:.2f}",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-an", str(out)], capture_output=True)
        if out.exists() and out.stat().st_size > 25000: return out, q
    return None, None


def main() -> int:
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    tmp = Path(tempfile.mkdtemp()); seen = set(); got = {}
    for sid, q in Q.items():
        if sid not in al: continue
        slot = max(2.0, al[sid]["end"] - al[sid]["start"]) + 0.3
        out, used = fetch(sid, q, slot, tmp, seen)
        if out: got[sid] = out; print(f"  ✓ {sid} ({dur(out):.1f}с) «{used[:40]}»", flush=True)
        else: print(f"  ✗ {sid}", flush=True)

    import pymiere
    from pymiere.wrappers import time_from_seconds
    from services.premiere_template.timeline_ops import import_media
    v3 = pymiere.objects.app.project.activeSequence.videoTracks[2]
    placed = 0
    for sid, f in got.items():
        u = UNIQ / f"dwlogo_{sid}.mp4"
        if not (u.exists() and u.stat().st_size == f.stat().st_size): shutil.copy(f, u)
        it = import_media(u)
        if it is None: continue
        v3.overwriteClip(it, time_from_seconds(round(al[sid]["start"], 2))); placed += 1
    before = PRPROJ.stat().st_mtime
    pymiere.objects.app.project.save(); time.sleep(1.5)
    print(f"\nлоготип→V3: {placed}/{len(got)} | уник {len(seen)} | сейв {'✓' if PRPROJ.stat().st_mtime>before else '✗'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
