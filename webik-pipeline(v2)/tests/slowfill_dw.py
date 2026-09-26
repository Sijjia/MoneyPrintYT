"""Убирает видимый ЛУП в сценах, где клип короче слота: вместо повтора — slow-mo
растяжение исходника ровно под слот (для анимации незаметно при factor<=2.3).
Пере-рендерит и кладёт на V3."""
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
PROJECT = ROOT / "projects" / "2026-08-25_aysberg-dreamworks-lost-media-i-temnaya-skrytaya-storona-stu"
VID = PROJECT / "assets" / "video_stock"
OUT = VID / "_slow"
OUT.mkdir(parents=True, exist_ok=True)


def dur(f):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                       capture_output=True, text=True)
    try: return float(r.stdout.strip())
    except: return 0


def main() -> int:
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    man = json.loads((PROJECT / "assets" / "images" / "manifest.json").read_text(encoding="utf-8"))
    fixed_sids = {p.stem for p in (VID / "_fixed").glob("*.mp4")}  # уже пере-фетчены (B.O.O./лупы) — не трогаем
    targets = []
    for sid, v in man.items():
        if v.get("kind") != "video" or sid not in al or sid in fixed_sids: continue
        slot = al[sid]["end"] - al[sid]["start"] + 0.3
        src = VID / os.path.basename(v.get("path", ""))
        if not src.exists(): continue
        d = dur(src)
        if d <= 0: continue
        f = slot / d
        if 1.08 < f <= 2.3:  # мягкий/средний луп → slow-mo
            targets.append((sid, src, d, slot, f))
    print(f"к slow-mo: {len(targets)}")

    built = {}
    for sid, src, d, slot, f in targets:
        outp = OUT / f"{sid}.mp4"
        if outp.exists() and abs(dur(outp) - slot) < 0.5:
            built[sid] = outp; continue
        subprocess.run(["ffmpeg", "-y", "-i", str(src),
                        "-vf", f"setpts={f:.4f}*PTS,scale=1920:1080:flags=lanczos",
                        "-t", f"{slot:.2f}", "-r", "30",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-an", str(outp)],
                       capture_output=True, text=True)
        if outp.exists() and outp.stat().st_size > 20000:
            built[sid] = outp
            if len(built) % 10 == 0: print(f"  ...{len(built)}/{len(targets)}", flush=True)
    print(f"пере-рендерено: {len(built)}")

    import pymiere
    from pymiere.wrappers import time_from_seconds
    from services.premiere_template.timeline_ops import import_media
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[2]
    placed = 0
    for sid, outp in sorted(built.items(), key=lambda kv: al[kv[0]]["start"]):
        try:
            it = import_media(outp)
            if it is None: continue
            v3.overwriteClip(it, time_from_seconds(round(al[sid]["start"], 2)))
            placed += 1
            if placed % 10 == 0: print(f"  ...уложено {placed}", flush=True)
        except Exception as e:
            print(f"  ✗ {sid}: {str(e)[:50]}")
    pymiere.objects.app.project.save()
    print(f"\nslow-mo уложено на V3: {placed}/{len(built)}; проект сохранён")
    return 0


if __name__ == "__main__":
    sys.exit(main())
