"""Реальные архивные фото → Ken-Burns → V3. Батч 2: Нигерия / Саллекхана / Шакахола.
Включает флагнутую Айдаром сцену 85 (было generic «african family» → реальные
альмаджири-дети Нигерии).

crop: опц. (x,y,w,h в долях) — вырезать разный план из одного большого фото.
MODE=build / MODE=swap.
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

# scene_id: (start, dur, photo, desc, crop|None)
JOBS = {
    "scene_083": (477.83, 11.10, "nigeria_almajiri1.jpg", "альмаджири-дети Нигерии", None),
    "scene_085": (496.63, 14.80, "nigeria_almajiri2.jpg", "альмаджири-дети (родители отдают)", None),
    "scene_090": (558.03, 13.30, "jain_temple.jpg", "джайнский храм Ранакпур", None),
    "scene_092": (579.90, 13.63, "jain_nun.jpg", "пожилая джайнская монахиня", None),
    "scene_093": (593.53, 16.27, "jain_temple.jpg", "храм — колонны (деталь)", (0.30, 0.30, 0.45, 0.55)),
    "scene_095": (624.43, 19.00, "jain_pilgrimage.jpg", "джайнский паломнический путь", None),
    "scene_109": (771.17, 14.40, "shakahola_kilifi.jpg", "Килифи (округ Шакахолы)", None),
}
ONLY = [s.strip() for s in os.environ.get("ONLY", "").split(",") if s.strip()]


def kenburns(img: Path, dur: float, out: Path, crop=None) -> bool:
    frames = int((dur + 0.6) * 30)
    pre = ""
    if crop:
        x, y, w, h = crop
        pre = f"crop=iw*{w}:ih*{h}:iw*{x}:ih*{y},"
    vf = (
        f"{pre}scale=2560:1440:force_original_aspect_ratio=increase,crop=2560:1440,"
        f"zoompan=z='min(zoom+0.0004,1.12)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30,"
        f"eq=saturation=0.58:contrast=1.12:brightness=-0.03:gamma=0.96,"
        f"noise=alls=11:allf=t+u,vignette=PI/4.7,format=yuv420p"
    )
    cmd = ["ffmpeg", "-y", "-loop", "1", "-i", str(img), "-t", f"{dur + 0.5:.2f}",
           "-vf", vf, "-r", "30", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("   ffmpeg:", r.stderr[-160:])
    return r.returncode == 0 and out.exists()


def build() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for sid, (_, dur, photo, desc, crop) in JOBS.items():
        if ONLY and sid not in ONLY:
            continue
        img = PHOTOS / photo
        if not img.exists():
            print(f"  {sid}: нет фото {photo}"); continue
        out = OUT / f"{sid}_real.mp4"
        if kenburns(img, dur, out, crop):
            subprocess.run(["ffmpeg", "-y", "-ss", f"{min(1.0,dur/2):.1f}", "-i", str(out), "-frames:v", "1",
                            "-vf", "scale=440:-1", str(FRAMES / f"b2_{sid}.png")], capture_output=True)
            print(f"  {sid}: {desc}")
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
            print(f"  {sid}: → {real.name}")
        except Exception as e:
            print(f"  {sid}: упал: {e}")
    pymiere.objects.app.project.save()
    print(f"подменено {swapped}, сохранено")
    return 0


if __name__ == "__main__":
    raise SystemExit(build() if os.environ.get("MODE", "build") == "build" else swap())
