"""Реальная YouTube-хроника Грабового на сцену 035 (его выступление/персона).

Источник: ранняя лекция Грабового (VHS-таймкод в кадре = подлинная хроника),
кэш-секция уже скачана. Режем окно, лёгкий грейд под палитру ролика, changeMediaPath
на V3 — позиции клипов (правки Айдара) не трогаем.

MODE=build — сделать клип + кадр
MODE=swap  — подменить медиа на V3
"""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-"
CACHE = Path(r"C:\Users\aidar\AppData\Local\Temp\claude\C--Users-aidar-OneDrive--------------automotization-youtube\0a3edf5b-8f55-4b33-a918-972784adb4ef\scratchpad\yt_cache")
FRAMES = Path(r"C:\Users\aidar\AppData\Local\Temp\claude\C--Users-aidar-OneDrive--------------automotization-youtube\0a3edf5b-8f55-4b33-a918-972784adb4ef\scratchpad\introchk")
SRC = CACHE / "201a3b43bc90_10_70.mp4"  # ранняя лекция, файл-время 0-60

# scene_id: (start_на_V3, окно_в_файле [f0,f1], slot_len)
JOBS = {
    "scene_035": (301.50, (5.0, 20.0), 13.06),
}
OUT = PROJECT / "assets" / "archive_clips"

# лёгкий архив-грейд: приглушить VHS-цвет, притемнить, красный тинт, виньетка
GRADE = (
    "eq=saturation=0.52:contrast=1.12:brightness=-0.06:gamma=0.95,"
    "colorbalance=rm=0.05:bm=-0.05,"
    "vignette=PI/4.8,"
    "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
    "format=yuv420p"
)


def build() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for sid, (_, (f0, f1), slot) in JOBS.items():
        out = OUT / f"{sid}_yt.mp4"
        dur = max(f1 - f0, slot + 1.0)
        cmd = [
            "ffmpeg", "-y", "-ss", f"{f0:.2f}", "-i", str(SRC), "-t", f"{dur:.2f}",
            "-an", "-vf", GRADE, "-r", "30", "-c:v", "libx264", "-crf", "20",
            "-pix_fmt", "yuv420p", str(out),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0 or not out.exists():
            print(f"  {sid}: грейд упал: {r.stderr[-200:]}")
            continue
        subprocess.run(["ffmpeg", "-y", "-ss", "3", "-i", str(out), "-frames:v", "1",
                        "-vf", "scale=720:-1", str(FRAMES / f"yt_{sid}.png")], capture_output=True)
        print(f"  {sid}: готов → {out.name}")
    return 0


def swap() -> int:
    import pymiere
    from services.premiere_template import timeline_ops  # noqa: F401
    from services.premiere_template.media_swap import ensure_premiere_open
    ensure_premiere_open(PROJECT / "project_template.prproj")
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[2]
    swapped = 0
    for sid, (start, _, _) in JOBS.items():
        arch = OUT / f"{sid}_yt.mp4"
        if not arch.exists():
            print(f"  {sid}: нет {arch.name}"); continue
        clip = None
        for i in range(v3.clips.numItems):
            c = v3.clips[i]
            if abs(c.start.seconds - start) < 0.4:
                clip = c; break
        if clip is None:
            print(f"  {sid}: клип @{start} не найден"); continue
        try:
            clip.projectItem.changeMediaPath(str(arch.resolve()), True)
            swapped += 1
            print(f"  {sid}: медиа → {arch.name}")
        except Exception as e:
            print(f"  {sid}: changeMediaPath упал: {e}")
    try:
        pymiere.objects.app.project.refreshMedia()
    except Exception:
        pass
    pymiere.objects.app.project.save()
    print(f"подменено {swapped}, сохранено")
    return 0


if __name__ == "__main__":
    raise SystemExit(build() if os.environ.get("MODE", "build") == "build" else swap())
