"""Архивные медиа на скучные стоки темы «Царская Империя» (Власов), 3:43–4:56.

Реальных свободных фото Власова/секты НЕТ (проверено). Поэтому берём атмосферное
видео под смысл сцены и накладываем АРХИВНЫЙ грейд (обесцвечивание+зерно+виньетка+
контраст) — с низким разрешением читается как документальная хроника.

MODE=source  — скачать с Pexels + грейд + кадры на ревью (без Premiere)
MODE=swap    — подменить медиа на V3 (changeMediaPath), только по одобренным сценам
"""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-"
RAW = PROJECT / "assets" / "archive_stock"
SCRATCH = Path(r"C:\Users\aidar\AppData\Local\Temp\claude\C--Users-aidar-OneDrive--------------automotization-youtube\0a3edf5b-8f55-4b33-a918-972784adb4ef\scratchpad\introchk")

# scene_id: (slot_dur, [pexels queries по приоритету], index)
SCENES = {
    "scene_027": (11.84, ["prison bars dark corridor", "empty jail cell", "barbed wire fence night"], 0),
    "scene_029": (7.80, ["people praying candles silhouette", "crowd candlelight vigil", "hands praying dark"], 0),
    "scene_031": (9.87, ["lonely silhouette fog", "man walking away cold street", "empty corridor light"], 0),
    "scene_032": (8.23, ["abandoned church interior", "empty cathedral dark", "old church candles"], 0),
    "scene_033": (16.20, ["crowd silhouette hands raised", "preacher congregation", "people looking up light"], 0),
}

# АРХИВНЫЙ грейд: выцветший цвет + зерно + виньетка + контраст
GRADE = (
    "eq=saturation=0.26:contrast=1.18:brightness=-0.02:gamma=0.95,"
    "colorbalance=rm=0.06:gm=0.02:bm=-0.05,"
    "noise=alls=15:allf=t+u,"
    "vignette=PI/4.6,"
    "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
    "format=yuv420p"
)


def source() -> int:
    from services.stocks.pexels_videos import PexelsVideosClient
    RAW.mkdir(parents=True, exist_ok=True)
    cli = PexelsVideosClient()
    for sid, (dur, queries, idx) in SCENES.items():
        raw = RAW / f"{sid}_raw.mp4"
        got = None
        for q in queries:
            try:
                got = cli.search_and_download(q, raw, index=idx, min_duration=4, max_duration=25)
            except Exception as e:
                print(f"  {sid}: '{q}' ошибка {e}")
                got = None
            if got and raw.exists() and raw.stat().st_size > 50_000:
                print(f"  {sid}: скачано по '{q}'")
                break
        if not got:
            print(f"  {sid}: НЕ НАЙДЕНО ни по одному запросу")
            continue
        out = RAW / f"{sid}_arch.mp4"
        cmd = [
            "ffmpeg", "-y", "-stream_loop", "-1", "-i", str(raw),
            "-t", f"{dur + 1.0:.2f}", "-an", "-vf", GRADE, "-r", "30",
            "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", str(out),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0 or not out.exists():
            print(f"  {sid}: грейд упал: {r.stderr[-200:]}")
            continue
        # кадр на ревью
        subprocess.run([
            "ffmpeg", "-y", "-ss", "2", "-i", str(out), "-frames:v", "1",
            "-vf", "scale=640:-1", str(SCRATCH / f"arch_{sid}.png"),
        ], capture_output=True)
        print(f"  {sid}: грейд готов → {out.name}")
    return 0


def swap() -> int:
    import pymiere
    from pymiere.wrappers import time_from_seconds  # noqa: F401
    from services.premiere_template import timeline_ops  # noqa: F401 (патч __del__)
    from services.premiere_template.media_swap import ensure_premiere_open

    approved = [s.strip() for s in os.environ.get("SWAP", "").split(",") if s.strip()]
    if not approved:
        print("SWAP пуст — укажи одобренные сцены: SWAP=scene_031,scene_032")
        return 1
    ensure_premiere_open(PROJECT / "project_template.prproj")
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[2]

    # старт сцены → клип на V3
    starts = {"scene_027": 223.43, "scene_029": 240.67, "scene_031": 262.33, "scene_032": 272.20, "scene_033": 280.47}
    swapped = 0
    for sid in approved:
        arch = RAW / f"{sid}_arch.mp4"
        if not arch.exists():
            print(f"  {sid}: нет {arch.name}, пропуск")
            continue
        target = starts[sid]
        clip = None
        for i in range(v3.clips.numItems):
            c = v3.clips[i]
            if abs(c.start.seconds - target) < 0.4:
                clip = c
                break
        if clip is None:
            print(f"  {sid}: клип на V3 @{target} не найден")
            continue
        pi = clip.projectItem
        try:
            pi.changeMediaPath(str(arch.resolve()), True)
            swapped += 1
            print(f"  {sid}: медиа подменено на {arch.name}")
        except Exception as e:
            print(f"  {sid}: changeMediaPath упал: {e}")
    try:
        pymiere.objects.app.project.refreshMedia()
    except Exception:
        pass
    pymiere.objects.app.project.save()
    print(f"подменено {swapped}, проект сохранён")
    return 0


if __name__ == "__main__":
    mode = os.environ.get("MODE", "source")
    raise SystemExit(source() if mode == "source" else swap())
