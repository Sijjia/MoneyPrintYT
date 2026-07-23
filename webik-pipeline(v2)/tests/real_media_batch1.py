"""Реальные архивные фото (Wikimedia Commons) → Ken-Burns архив-клипы → V3.
Батч 1: The Family / Colonia Dignidad / Китай / альбиносы Танзании.

MODE=build — Ken-Burns из фото + кадры на ревью
MODE=swap  — changeMediaPath на V3 (позиции Айдара не трогаем)
"""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-"
PHOTOS = PROJECT / "assets" / "real_photos"
OUT = PROJECT / "assets" / "archive_clips"
FRAMES = Path(r"C:\Users\aidar\AppData\Local\Temp\claude\C--Users-aidar-OneDrive--------------automotization-youtube\0a3edf5b-8f55-4b33-a918-972784adb4ef\scratchpad\introchk")

# scene_id: (timeline_start, slot_dur, photo, что это)
JOBS = {
    "scene_101": (711.83, 13.30, "family_Lake_Eildon_late_2011.jpg", "озеро Эйлдон (место рейда)"),
    "scene_104": (745.13, 2.34, "family_Sherbrooke_Forest.jpg", "лес Шербрук (сердце секты)"),
    "scene_170": (1239.13, 12.67, "colonia_hotel.jpg", "здание Colonia Dignidad"),
    "scene_171": (1252.13, 12.10, "colonia_villa.jpg", "Вилла Бавиера (колония)"),
    "scene_164": (1158.07, 20.96, "china_protest.jpg", "протест Фалуньгун"),
    "scene_177": (1330.47, 24.23, "albino_tz_school.jpg", "школьники-альбиносы, Танзания"),
    "scene_181": (1391.93, 10.57, "albino_salif.jpg", "Салиф Кейта (альбинос-адвокат)"),
}


def kenburns(img: Path, dur: float, out: Path) -> bool:
    frames = int((dur + 0.6) * 30)
    vf = (
        f"scale=2560:1440:force_original_aspect_ratio=increase,crop=2560:1440,"
        f"zoompan=z='min(zoom+0.0004,1.12)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30,"
        f"eq=saturation=0.58:contrast=1.12:brightness=-0.03:gamma=0.96,"
        f"noise=alls=11:allf=t+u,vignette=PI/4.7,format=yuv420p"
    )
    cmd = ["ffmpeg", "-y", "-loop", "1", "-i", str(img), "-t", f"{dur + 0.5:.2f}",
           "-vf", vf, "-r", "30", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode == 0 and out.exists()


def build() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for sid, (_, dur, photo, desc) in JOBS.items():
        img = PHOTOS / photo
        if not img.exists():
            print(f"  {sid}: нет фото {photo}"); continue
        out = OUT / f"{sid}_real.mp4"
        if kenburns(img, dur, out):
            subprocess.run(["ffmpeg", "-y", "-ss", f"{min(1.0,dur/2):.1f}", "-i", str(out), "-frames:v", "1",
                            "-vf", "scale=440:-1", str(FRAMES / f"real_{sid}.png")], capture_output=True)
            print(f"  {sid}: {desc} → {out.name}")
        else:
            print(f"  {sid}: Ken-Burns упал")
    return 0


def swap() -> int:
    import pymiere
    from services.premiere_template import timeline_ops  # noqa: F401
    from services.premiere_template.media_swap import ensure_premiere_open
    approved = [s.strip() for s in os.environ.get("SWAP", "").split(",") if s.strip()] or list(JOBS)
    ensure_premiere_open(PROJECT / "project_template.prproj")
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[2]
    swapped = 0
    for sid in approved:
        real = OUT / f"{sid}_real.mp4"
        if not real.exists():
            print(f"  {sid}: нет клипа"); continue
        start = JOBS[sid][0]
        clip = None
        for i in range(v3.clips.numItems):
            c = v3.clips[i]
            if abs(c.start.seconds - start) < 0.5:
                clip = c; break
        if clip is None:
            print(f"  {sid}: клип @{start} не найден"); continue
        try:
            clip.projectItem.changeMediaPath(str(real.resolve()), True)
            swapped += 1
            print(f"  {sid}: медиа → {real.name}")
        except Exception as e:
            print(f"  {sid}: упал: {e}")
    pymiere.objects.app.project.save()
    print(f"подменено {swapped}, сохранено")
    return 0


if __name__ == "__main__":
    raise SystemExit(build() if os.environ.get("MODE", "build") == "build" else swap())
