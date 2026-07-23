"""Переделка медиа Индонезии: вместо пейзажей — тёмные ФИГУРЫ-угроза («ниндзя»).

Тема: убийцы в масках и чёрном, по ночам, эскадроны смерти. Нужны силуэты,
капюшоны, факелы — не деревни. Без графики (никакого насилия/трупов).

MODE=source / MODE=swap. Грейд архивный. changeMediaPath на V3.
"""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-"
RAW = PROJECT / "assets" / "archive_stock"
FRAMES = Path(r"C:\Users\aidar\AppData\Local\Temp\claude\C--Users-aidar-OneDrive--------------automotization-youtube\0a3edf5b-8f55-4b33-a918-972784adb4ef\scratchpad\introchk")

# фигуры/маски/факелы под смысл «ниндзя»-охоты
SCENES = {
    "scene_076": (398.00, 13.60, ["silhouette figures walking fog", "dark figures fog forest", "shadow people walking fog night"]),
    "scene_077": (411.60, 12.83, ["hooded figure black night", "masked person hood dark night", "person black hood shadow fog"]),
    "scene_078": (424.97, 8.40, ["people holding torches night", "silhouette figures torch night", "torch crowd night dark"]),
    "scene_080": (443.10, 13.23, ["fire torch procession night", "people torches march night", "night fire crowd silhouette"]),
}

GRADE = (
    "eq=saturation=0.3:contrast=1.18:brightness=-0.05:gamma=0.94,"
    "colorbalance=rm=0.06:bm=-0.05,"
    "noise=alls=14:allf=t+u,"
    "vignette=PI/4.5,"
    "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
    "format=yuv420p"
)


def source() -> int:
    from services.stocks.pexels_videos import PexelsVideosClient
    RAW.mkdir(parents=True, exist_ok=True)
    cli = PexelsVideosClient()
    for sid, (_, dur, queries) in SCENES.items():
        raw = RAW / f"{sid}_fig_raw.mp4"
        got = None
        chosen_q = ""
        for q in queries:
            try:
                got = cli.search_and_download(q, raw, index=0, min_duration=4, max_duration=30)
            except Exception as e:
                print(f"  {sid}: '{q}' err {e}"); got = None
            if got and raw.exists() and raw.stat().st_size > 50_000:
                chosen_q = q; break
        if not got:
            print(f"  {sid}: НЕ НАЙДЕНО"); continue
        out = RAW / f"{sid}_fig.mp4"
        cmd = ["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(raw), "-t", f"{dur + 1.0:.2f}",
               "-an", "-vf", GRADE, "-r", "30", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", str(out)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0 or not out.exists():
            print(f"  {sid}: грейд упал: {r.stderr[-160:]}"); continue
        subprocess.run(["ffmpeg", "-y", "-ss", "2", "-i", str(out), "-frames:v", "1",
                        "-vf", "scale=520:-1", str(FRAMES / f"fig_{sid}.png")], capture_output=True)
        print(f"  {sid}: '{chosen_q}' готов")
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
        arch = RAW / f"{sid}_fig.mp4"
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
