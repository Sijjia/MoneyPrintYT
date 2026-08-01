"""Пересобирает медиа хвоста Ордена (184,186,187,188,189) РАЗНЫМИ тематическими
кадрами через Pexels (атмосфера — визуально не похожи друг на друга), с лупом до
длины сцены + DNxHR. БЕЗ Premiere. Расстановка — tail_media_place.py (тянет из tail_media).
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.stocks.pexels_videos import PexelsVideosClient as PexelsVideos
from tests.cutaway_source_place import normalize, PROJECT

OUT = (PROJECT / "assets" / "tail_media").resolve()
CACHE = (PROJECT / "assets" / "_pexels_cache").resolve()

# (scene, start, dur, [запросы по приоритету]) — РАЗНЫЕ визуалы под смысл
JOBS = [
    ("scene_184", 1384, 14.3, ["gothic cathedral interior candles dark", "dark church candlelight", "occult symbols candlelit"]),
    ("scene_186", 1408, 15.4, ["snowy forest cabin winter night", "dark winter forest snow", "isolated cabin snow woods"]),
    ("scene_187", 1424, 12.3, ["swiss alps chalet valley", "alpine wooden chalet mountains", "swiss mountain village fog"]),
    ("scene_188", 1436, 17.2, ["candles altar dark ritual", "hooded figures candle procession", "dark ceremony candlelight"]),
    ("scene_189", 1453, 13.2, ["aerial snowy mountain peaks winter", "french alps snowy mountains", "cold mountain summit clouds"]),
]


def loopfill(src: Path, dur: float, tag: str) -> Path:
    """Если исходник короче dur — зациклить до нужной длины."""
    d = 0.0
    try:
        d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                  "-of", "csv=p=0", str(src)], capture_output=True, text=True).stdout.strip() or 0)
    except Exception:
        pass
    if d >= dur - 0.5:
        return src
    dst = CACHE / f"{tag}_loop.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "-1", "-i", str(src),
                    "-t", f"{dur:.2f}", "-c", "copy", str(dst)], check=False)
    return dst if dst.exists() else src


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True); CACHE.mkdir(parents=True, exist_ok=True)
    px = PexelsVideos()
    ok = 0
    for sid, start, dur, queries in JOBS:
        dst = OUT / f"{sid}_{start}.mov"
        if dst.exists():
            dst.unlink()
        raw = None
        for qi, q in enumerate(queries):
            print(f"{sid} :: '{q}'", flush=True)
            try:
                p = px.search_and_download(q, CACHE / f"{sid}_{start}_{qi}.mp4", index=0, min_duration=6)
                if p and Path(p).exists() and Path(p).stat().st_size > 10000:
                    raw = Path(p); print("    скачано"); break
            except Exception as e:
                print(f"    сбой: {str(e)[:80]}")
        if raw is None:
            print(f"    {sid}: нет клипа — пропуск"); continue
        src = loopfill(raw, dur, f"{sid}_{start}")
        if normalize(src, dst, dur):
            ok += 1; print(f"    ✓ {dst.name}")
    print(f"\nготово {ok}/{len(JOBS)} .mov")
    return 0


if __name__ == "__main__":
    sys.exit(main())
