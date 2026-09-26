"""Качает выбранные КИНОВСТАВКИ-отсылки (cutaways_dw.json) и кладёт короткими клипами на V8 (над графикой).
Фильтр: не над трагедией + не поверх уже стоящей графики. md5-дедуп. Префикс cut_."""
import hashlib, json, shutil, subprocess, sys, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
PROJECT = ROOT / "projects" / "2026-08-25_aysberg-dreamworks-lost-media-i-temnaya-skrytaya-storona-stu"
CUT = PROJECT / "assets" / "cutaways"; UNIQ = PROJECT / "assets" / "_uniq"
for d in (CUT, UNIQ): d.mkdir(parents=True, exist_ok=True)
YT = [str(ROOT.parent / "webik-pipeline" / ".venv" / "Scripts" / "python.exe"), "-m", "yt_dlp",
      "--no-warnings", "--extractor-args", "youtube:player_client=android"]
PRPROJ = PROJECT / "project_template.prproj"
TRAGEDY_DROP = {"scene_092", "scene_141", "scene_214"}  # смерть Фарли / геноцид панд / казнь первенцев


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


def fetch(sid, query, seconds, tmp, seen):
    for qi, q in enumerate([query, query + " scene", query + " clip HD"]):
        raw = tmp / f"{sid}_{qi}.mp4"
        subprocess.run(YT + ["--download-sections", "*6-24", "--force-keyframes-at-cuts",
                       "-o", str(raw), f"ytsearch1:{q}"], capture_output=True, text=True, timeout=200)
        if not raw.exists() or raw.stat().st_size < 25000: continue
        h = md5(raw)
        if h in seen: continue
        seen.add(h)
        out = CUT / f"cut_{sid}.mp4"
        # апскейл + обрезка до нужной длины (со 2-й секунды, чтобы пропустить возможную склейку кадра)
        subprocess.run(["ffmpeg", "-y", "-ss", "2", "-i", str(raw), "-t", f"{seconds:.2f}",
                        "-vf", "scale=1920:1080:flags=lanczos", "-c:v", "libx264", "-preset", "veryfast",
                        "-crf", "20", "-an", str(out)], capture_output=True)
        if out.exists() and out.stat().st_size > 25000: return out, q
    return None, None


def main() -> int:
    picks = json.loads((PROJECT / "cutaways_dw.json").read_text(encoding="utf-8"))
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    plan = json.loads((PROJECT / "graphics_plan_v2_dw.json").read_text(encoding="utf-8"))
    tmp = Path(tempfile.mkdtemp()); seen = set(); got = {}
    for r in sorted(picks, key=lambda x: al.get(x["id"], {}).get("start", 0)):
        sid = r["id"]
        if sid not in al: continue
        if sid in TRAGEDY_DROP: print(f"  – {sid} пропуск (трагедия)"); continue
        if sid in plan: print(f"  – {sid} пропуск (уже графика)"); continue
        sec = max(1.5, min(3.0, float(r.get("seconds", 2.0))))
        out, used = fetch(sid, r["query"], sec, tmp, seen)
        if out: got[sid] = (out, r); print(f"  ✓ {sid} {r.get('film')}: {r.get('moment','')[:32]} ({dur(out):.1f}с)", flush=True)
        else: print(f"  ✗ {sid} ({r.get('film')})", flush=True)

    import pymiere
    from pymiere.wrappers import time_from_seconds
    from services.premiere_template.timeline_ops import import_media
    v8 = pymiere.objects.app.project.activeSequence.videoTracks[7]
    placed = 0
    for sid, (f, r) in got.items():
        u = UNIQ / f"cut_{sid}.mp4"
        if not (u.exists() and u.stat().st_size == f.stat().st_size): shutil.copy(f, u)
        it = import_media(u)
        if it is None: continue
        v8.overwriteClip(it, time_from_seconds(round(al[sid]["start"], 2))); placed += 1
    before = PRPROJ.stat().st_mtime
    pymiere.objects.app.project.save(); time.sleep(1.5)
    print(f"\nвставок→V8: {placed}/{len(got)} | уник {len(seen)} | сейв {'✓' if PRPROJ.stat().st_mtime>before else '✗'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
