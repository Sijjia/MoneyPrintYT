"""Архивная яванская натура на скучные стоки темы Индонезии (6:29–7:46).

YouTube-загрузка Алас-Пурво не пошла (ютуб режет после первого клипа). Берём
атмосферную тропическую натуру Pexels + архивный грейд — под смысл сцен.

MODE=source — скачать + грейд + кадры на ревью
MODE=swap   — changeMediaPath на V3 (позиции клипов Айдара не трогаем)
"""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-"
RAW = PROJECT / "assets" / "archive_stock"
FRAMES = Path(r"C:\Users\aidar\AppData\Local\Temp\claude\C--Users-aidar-OneDrive--------------automotization-youtube\0a3edf5b-8f55-4b33-a918-972784adb4ef\scratchpad\introchk")

# scene_id: (timeline_start, slot_dur, [queries])
SCENES = {
    "scene_076": (389.07, 22.46, ["aerial rural village asia night", "indonesia village aerial", "tropical village houses dusk"]),
    "scene_078": (424.97, 8.40, ["foggy village houses night", "asian village fog night", "dark village street night"]),
    "scene_079": (433.63, 9.20, ["misty tropical rainforest fog", "dark jungle fog mist", "foggy forest dark"]),
    "scene_080": (443.10, 13.23, ["torch procession night", "fire ritual night crowd", "candle procession night"]),
    "scene_081": (456.33, 10.47, ["candles ritual night dark", "traditional ceremony candles night", "candlelight ritual dark"]),
}

GRADE = (
    "eq=saturation=0.3:contrast=1.17:brightness=-0.04:gamma=0.95,"
    "colorbalance=rm=0.05:bm=-0.05,"
    "noise=alls=14:allf=t+u,"
    "vignette=PI/4.6,"
    "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
    "format=yuv420p"
)


def source() -> int:
    from services.stocks.pexels_videos import PexelsVideosClient
    RAW.mkdir(parents=True, exist_ok=True)
    cli = PexelsVideosClient()
    for sid, (_, dur, queries) in SCENES.items():
        raw = RAW / f"{sid}_raw.mp4"
        got = None
        for q in queries:
            try:
                got = cli.search_and_download(q, raw, index=0, min_duration=4, max_duration=30)
            except Exception as e:
                print(f"  {sid}: '{q}' err {e}"); got = None
            if got and raw.exists() and raw.stat().st_size > 50_000:
                print(f"  {sid}: '{q}'"); break
        if not got:
            print(f"  {sid}: НЕ НАЙДЕНО"); continue
        out = RAW / f"{sid}_arch.mp4"
        cmd = ["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(raw), "-t", f"{dur + 1.0:.2f}",
               "-an", "-vf", GRADE, "-r", "30", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", str(out)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0 or not out.exists():
            print(f"  {sid}: грейд упал: {r.stderr[-160:]}"); continue
        subprocess.run(["ffmpeg", "-y", "-ss", "2", "-i", str(out), "-frames:v", "1",
                        "-vf", "scale=520:-1", str(FRAMES / f"ind_{sid}.png")], capture_output=True)
        print(f"  {sid}: готов")
    return 0


def swap() -> int:
    import pymiere
    from services.premiere_template import timeline_ops  # noqa: F401
    from services.premiere_template.media_swap import ensure_premiere_open
    approved = [s.strip() for s in os.environ.get("SWAP", "").split(",") if s.strip()]
    if not approved:
        print("SWAP пуст"); return 1
    ensure_premiere_open(PROJECT / "project_template.prproj")
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[2]
    swapped = 0
    for sid in approved:
        arch = RAW / f"{sid}_arch.mp4"
        if not arch.exists():
            print(f"  {sid}: нет файла"); continue
        start = SCENES[sid][0]
        clip = None
        for i in range(v3.clips.numItems):
            c = v3.clips[i]
            if abs(c.start.seconds - start) < 0.5:
                clip = c; break
        if clip is None:
            print(f"  {sid}: клип @{start} не найден"); continue
        try:
            clip.projectItem.changeMediaPath(str(arch.resolve()), True)
            swapped += 1
            print(f"  {sid}: медиа → {arch.name}")
        except Exception as e:
            print(f"  {sid}: упал: {e}")
    pymiere.objects.app.project.save()
    print(f"подменено {swapped}, сохранено")
    return 0


if __name__ == "__main__":
    raise SystemExit(source() if os.environ.get("MODE", "source") == "source" else swap())
