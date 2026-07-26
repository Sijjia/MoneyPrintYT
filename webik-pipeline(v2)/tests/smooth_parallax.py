"""Заменяет параллакс-клипы (2.5D «плывёт») на ПЛАВНЫЙ Ken-Burns из того же фото:
равномерный зум на высоком разрешении → без искажений и джиттера. changeMediaPath на V3.

MODE=build — Ken-Burns + кадры-пробы; MODE=swap — подмена на V3.
Сцены под интро (start<59с) пропускаем.
"""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-"
OUT = PROJECT / "assets" / "kenburns"
FRAMES = Path(r"C:\Users\aidar\AppData\Local\Temp\claude\C--Users-aidar-OneDrive--------------automotization-youtube\0a3edf5b-8f55-4b33-a918-972784adb4ef\scratchpad\introchk")


def load():
    import json
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    jobs = []
    for line in (PROJECT / "_parallax_list.txt").read_text(encoding="utf-8").splitlines():
        sid, src, img, dur = line.split("|")
        st = al.get(sid, {}).get("start", 0)
        if st < 59:  # под интро — пропуск
            continue
        jobs.append((sid, img, float(dur)))
    return jobs


def kenburns(img: Path, dur: float, out: Path) -> bool:
    frames = int((dur + 0.6) * 30)
    vf = (
        f"scale=2880:1620:force_original_aspect_ratio=increase,crop=2880:1620,"
        f"zoompan=z='min(1.001+on/{frames}*0.07,1.07)':d={frames}:"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30,"
        f"eq=saturation=0.72:contrast=1.08:brightness=-0.02,"
        f"noise=alls=6:allf=t,vignette=PI/5,format=yuv420p"
    )
    cmd = ["ffmpeg", "-y", "-loop", "1", "-i", str(img), "-t", f"{dur + 0.5:.2f}",
           "-vf", vf, "-r", "30", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode == 0 and out.exists()


def build() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = load()
    print(f"сцен к сглаживанию: {len(jobs)}")
    ok = 0
    for sid, img, dur in jobs:
        p = PROJECT / img
        if not p.exists():
            print(f"  {sid}: нет {img}"); continue
        out = OUT / f"{sid}_kb.mp4"
        if kenburns(p, dur, out):
            ok += 1
            if ok <= 4:
                subprocess.run(["ffmpeg", "-y", "-ss", str(min(1.0, dur / 2)), "-i", str(out),
                                "-frames:v", "1", "-vf", "scale=440:-1", str(FRAMES / f"kb_{sid}.png")], capture_output=True)
    print(f"готово {ok}/{len(jobs)}")
    return 0


def swap() -> int:
    import pymiere
    from services.premiere_template import timeline_ops  # noqa: F401
    from services.premiere_template.media_swap import ensure_premiere_open
    ensure_premiere_open(PROJECT / "project_template.prproj")
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[2]
    import re
    byname = {}
    for i in range(v3.clips.numItems):
        c = v3.clips[i]
        mm = re.match(r"(scene_\d+)", c.name)
        if mm:
            byname.setdefault(mm.group(1), c)
    jobs = load()
    sw, miss = 0, []
    for sid, img, dur in jobs:
        kb = OUT / f"{sid}_kb.mp4"
        if not kb.exists():
            continue
        c = byname.get(sid)
        if c is None:
            miss.append(sid); continue
        try:
            c.projectItem.changeMediaPath(str(kb.resolve()), True)
            sw += 1
        except Exception as e:
            print(f"  {sid}: {e}")
    pymiere.objects.app.project.save()
    print(f"сглажено (подменено) {sw}; не найдены: {miss}")
    return 0


if __name__ == "__main__":
    sys.exit(build() if os.environ.get("MODE", "build") == "build" else swap())
