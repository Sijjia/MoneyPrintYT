"""Точечная замена медиа scene_012 (r/nosleep: чужаки принимают вымысел за правду, звонят в
полицию / пишут тревожные посты) на интересный тематический футаж c Pexels. Без пересборки:
качаем → нормализуем в точную длину слота (1920x1080@30) → overwrite на V3 → правим манифест."""
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
from pymiere.wrappers import time_from_seconds
from services.stocks.pexels_videos import PexelsVideosClient
from services.premiere_template.timeline_ops import import_media

P = ROOT / "projects" / "2026-09-13_aysberg-reddit-strannaya-i-trevozhnaya-storona"
SID = "scene_012"
CACHE = (P / "assets" / "_pexels_cache").resolve(); CACHE.mkdir(parents=True, exist_ok=True)
NEW = (P / "assets" / "video_stock" / f"{SID}_new.mp4").resolve()
MAN = P / "assets" / "images" / "manifest.json"

# по смыслу: тревожный ночной звонок в полицию / диспетчер экстренной службы (динамично, по теме)
QUERIES = ["emergency dispatcher call center headset", "person calling phone worried night dark",
           "911 operator emergency call", "police car lights night street", "anxious phone call dark room"]


def loopfill(src: Path, dur: float) -> Path:
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                              "-of", "csv=p=0", str(src)], capture_output=True, text=True).stdout.strip() or 0)
    if d >= dur - 0.3:
        return src
    dst = CACHE / f"{SID}_loop.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "-1", "-i", str(src),
                    "-t", f"{dur:.2f}", "-c", "copy", str(dst)], check=False)
    return dst if dst.exists() else src


def normalize(src: Path, dst: Path, dur: float) -> bool:
    vf = ("scale=1920:1080:force_original_aspect_ratio=increase,crop=1728:972,scale=1920:1080,"
          "eq=saturation=0.96:contrast=1.04,setsar=1,fps=30,"
          f"fade=t=in:st=0:d=0.3,fade=t=out:st={max(0.3,dur-0.4):.2f}:d=0.4")
    r = subprocess.run(["ffmpeg", "-y", "-i", str(src), "-t", f"{dur:.3f}", "-an", "-vf", vf, "-r", "30",
                        "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", str(dst)],
                       capture_output=True, text=True)
    return r.returncode == 0 and dst.exists() and dst.stat().st_size > 40000


def main() -> int:
    al = json.loads((P / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    st = al[SID]["start"]
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[2]
    clip = min(v3.clips, key=lambda c: abs(c.start.seconds - st))
    t0 = clip.start.seconds
    slot = clip.end.seconds - clip.start.seconds
    print(f"{SID}: слот {t0:.2f}-{clip.end.seconds:.2f} ({slot:.2f}с)", flush=True)

    px = PexelsVideosClient()
    raw = None
    for q in QUERIES:
        try:
            p = px.search_and_download(q, CACHE / f"{SID}_dl.mp4", index=0, min_duration=5)
            if p and Path(p).exists() and Path(p).stat().st_size > 10000:
                raw = Path(p); print(f"  скачано: '{q}'", flush=True); break
        except Exception as e:
            print(f"  сбой '{q}': {str(e)[:60]}", flush=True)
    if raw is None:
        print("нет клипа"); return 1

    src = loopfill(raw, slot)
    if NEW.exists():
        NEW.unlink()
    if not normalize(src, NEW, slot):
        print("normalize упал"); return 1

    item = import_media(NEW)
    if item is None:
        print("import упал"); return 1
    v3.overwriteClip(item, time_from_seconds(t0))

    man = json.loads(MAN.read_text(encoding="utf-8"))
    man[SID] = {"path": str(NEW), "query": f"pexels: {QUERIES[0]}", "kind": "video", "source": "pexels-video"}
    MAN.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    pymiere.objects.app.project.save()
    print(f"✓ {SID} заменён на тематический футаж, уложен @ {t0:.2f}, сохранено", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
