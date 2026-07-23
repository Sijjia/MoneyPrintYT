"""Скачивает окна-пробы кандидатов Грабового и раскладывает кадры на ревью."""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.stocks.youtube_clipper import download_section

CACHE = Path(r"C:\Users\aidar\AppData\Local\Temp\claude\C--Users-aidar-OneDrive--------------automotization-youtube\0a3edf5b-8f55-4b33-a918-972784adb4ef\scratchpad\yt_cache")
FRAMES = Path(r"C:\Users\aidar\AppData\Local\Temp\claude\C--Users-aidar-OneDrive--------------automotization-youtube\0a3edf5b-8f55-4b33-a918-972784adb4ef\scratchpad\introchk")

# метка → (url, start, end)
PROBES = {
    "lec_early": ("https://www.youtube.com/watch?v=zWbxITZgbjU", 10, 70),
    "lec_gtv": ("https://www.youtube.com/watch?v=I4A9hh2e5Nc", 20, 80),
    "web_now": ("https://www.youtube.com/watch?v=iD0-IPyYvj4", 15, 75),
}


def main() -> int:
    for tag, (url, s, e) in PROBES.items():
        print(f"== {tag}: {url} [{s}-{e}]")
        sec = download_section(url, CACHE, s, e)
        if not sec:
            print(f"   не скачалось")
            continue
        print(f"   → {sec.name} ({sec.stat().st_size//1024} KB)")
        # 4 кадра равномерно
        subprocess.run([
            "ffmpeg", "-y", "-i", str(sec),
            "-vf", "select='not(mod(n\\,220))',scale=360:-1,tile=4x1",
            "-frames:v", "1", str(FRAMES / f"probe_{tag}.png"),
        ], capture_output=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
