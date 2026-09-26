"""Финализация двух последних тем: дозаменить 215/217 футажём, проставить манифест для всех
уже-уложенных (211/213/214/221) и сохранить. Один инстанс."""
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
from pymiere.wrappers import time_from_seconds
from services.stocks.pexels_videos import PexelsVideosClient
from services.premiere_template.timeline_ops import import_media

P = ROOT / "projects" / "2026-09-13_aysberg-reddit-strannaya-i-trevozhnaya-storona"
VS = P / "assets" / "video_stock"
GFX = P / "assets" / "gfx"
CACHE = (P / "assets" / "_pexels_cache").resolve()
MANIFEST = P / "assets" / "images" / "manifest.json"
FPS = 30

# уже на таймлайне — только манифест
PLACED = {
    "scene_211": ("docuframe", GFX / "scene_211_gfx.mp4", "web: «The end of ReligionOfPeace»"),
    "scene_213": ("docuframe", GFX / "scene_213_gfx.mp4", "web: Профиль AngelTwo-Six — откуда имя"),
    "scene_221": ("docuframe", GFX / "scene_221_gfx.mp4", "web: Разбор на канале Whang! (2020)"),
    "scene_214": ("pexels-video", VS / "scene_214_reb.mp4", "pexels: classified redacted documents"),
}
FOOT = [
    ("scene_215", ["special forces soldiers silhouette night", "military tactical team dark", "surveillance dark room monitors"]),
    ("scene_217", ["deleting files computer screen dark", "server room powering down dark", "empty desk case file dim light"]),
]


def containing_clip(v3, mid):
    best = None
    for c in v3.clips:
        if c.start.seconds - 0.05 <= mid < c.end.seconds + 0.05:
            best = c
    return best or min(v3.clips, key=lambda c: abs(c.start.seconds - mid))


def loopfill(src, dur, tag):
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                              "-of", "csv=p=0", str(src)], capture_output=True, text=True).stdout.strip() or 0)
    if d >= dur - 0.3: return src
    dst = CACHE / f"{tag}_loop.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "-1", "-i", str(src),
                    "-t", f"{dur:.2f}", "-c", "copy", str(dst)], check=False)
    return dst if dst.exists() else src


def normalize(src, dst, dur):
    vf = ("scale=1920:1080:force_original_aspect_ratio=increase,crop=1728:972,scale=1920:1080,"
          "eq=saturation=0.92:contrast=1.05,setsar=1,fps=30,"
          f"fade=t=in:st=0:d=0.3,fade=t=out:st={max(0.3,dur-0.4):.2f}:d=0.4")
    r = subprocess.run(["ffmpeg", "-y", "-i", str(src), "-t", f"{dur:.3f}", "-an", "-vf", vf, "-r", "30",
                        "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", str(dst)], capture_output=True, text=True)
    return r.returncode == 0 and dst.exists() and dst.stat().st_size > 40000


def main() -> int:
    al = json.loads((P / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[2]

    for sid, (src, path, q) in PLACED.items():
        if path.exists():
            man[sid] = {"path": str(path.resolve()), "query": q, "kind": "video", "source": src}
            print(f"  man {sid} = {src}", flush=True)

    px = PexelsVideosClient()
    for sid, queries in FOOT:
        mid = al[sid]["start"] + 0.3
        clip = containing_clip(v3, mid); t0 = clip.start.seconds
        dur = clip.end.seconds - clip.start.seconds
        raw = None
        for qi, q in enumerate(queries):
            try:
                p = px.search_and_download(q, CACHE / f"{sid}_{qi}.mp4", index=0, min_duration=5)
                if p and Path(p).exists() and Path(p).stat().st_size > 10000:
                    raw = Path(p); print(f"  {sid}: pexels «{q}»", flush=True); break
            except Exception as e:
                print(f"  {sid} '{q}': {str(e)[:50]}", flush=True)
        if raw is None:
            print(f"  x {sid}: no footage", flush=True); continue
        dst = VS / f"{sid}_reb.mp4"
        if dst.exists(): dst.unlink()
        if not normalize(loopfill(raw, dur, sid), dst, dur):
            print(f"  x {sid}: normalize fail", flush=True); continue
        item = import_media(dst.resolve())
        if item is None:
            print(f"  x {sid}: import fail", flush=True); continue
        v3.overwriteClip(item, time_from_seconds(t0))
        man[sid] = {"path": str(dst.resolve()), "query": f"pexels: {queries[0]}", "kind": "video", "source": "pexels-video"}
        print(f"  OK {sid} @ {t0:.1f} ({dur:.1f}s)", flush=True)

    MANIFEST.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    pymiere.objects.app.project.save()
    print("DONE saved", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
