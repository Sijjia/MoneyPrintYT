"""Демо авто-привязки архивных клипов по сценам через archive_clip_placer.

Берёт уже скачанный демо-клип ЧАЭС, делает мини-manifest с привязкой к
scene_004, и кладёт его НА СЛОТ сцены (из alignment) реальной продакшен-
функцией place_archive_clips (трим под окно + mute + fade). Premiere должен
быть открыт на проекте iceberg.

Запуск:
  PYTHONIOENCODING=utf-8 ../webik-pipeline/.venv/Scripts/python.exe tests/archive_autobind_demo.py
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.premiere_template.media_swap import ensure_premiere_open, current_project_path
from services.premiere_template.timeline_ops import clear_track_es
from services.premiere.archive_clip_placer import place_archive_clips
from pymiere import objects as p

PROJECT_DIR = Path(__file__).resolve().parent.parent / "projects" / "iceberg-4-levels-test"
CUTAWAY_IDX = 5  # V6

def main():
    ensure_premiere_open()
    proj = current_project_path()
    assert proj and "iceberg-4-levels-test" in str(proj), f"не тот проект: {proj}"

    alignment = json.loads((PROJECT_DIR / "assets" / "alignment.json").read_text(encoding="utf-8"))
    scene_timings = alignment["scenes"]

    # мини-manifest как его записал бы Stage 4 (тир youtube-auto)
    manifest = {
        "scene_004": {
            "path": "assets/youtube_clips/yt_demo_chernobyl.mp4",
            "query": "Чернобыль ликвидация 1986",
            "kind": "video",
            "source": "youtube-auto",
        }
    }

    seq = p.app.project.activeSequence
    # убрать ручной демо-клип из прошлого шага
    removed = clear_track_es("videoTracks", CUTAWAY_IDX)
    print(f"V{CUTAWAY_IDX+1} очищена: убрано {removed}")

    t = scene_timings["scene_004"]
    print(f"scene_004 окно: {t['start']:.2f}-{t['end']:.2f}s")

    n = place_archive_clips(seq, manifest, scene_timings, PROJECT_DIR, track_idx=CUTAWAY_IDX)
    print(f"размещено архив-клипов: {n}")

    # верификация
    tr = seq.videoTracks[CUTAWAY_IDX]
    for i in range(tr.clips.numItems):
        c = tr.clips[i]
        print(f"  V{CUTAWAY_IDX+1}[{i}] '{c.name}' {c.start.seconds:.2f}-{c.end.seconds:.2f}s")
    print("DONE — не сохранял, смотри в Premiere")

if __name__ == "__main__":
    main()
