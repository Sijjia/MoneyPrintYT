"""Перерендер карты Индонезии в СВЕЖУЮ папку (старый файл лочит Premiere):
подписи городов налезали → имена в заголовок, точки без подписей.
Снимаем старый клип arch_i2 с V8, кладём новый.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pymiere
from services.overlays.render_bridge import render_overlays
from services.premiere.overlay_placer import place_overlays

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-"
ACCENT = "#d92828"

MAP = {
    "id": "arch_i2",
    "type": "mapspread",
    "composition": "MapSpread",
    "scene_id": "scene_076",
    "start": 390.0,
    "duration_sec": 8.0,
    "anchor": "волна массовых линчеваний по Баньюванги и Джембер",
    "props": {
        "title": "Баньюванги · Джембер · 1998",
        "label": "Ночная охота на «колдунов»",
        "durationInFrames": 240,
        "accent": ACCENT,
        "origins": [
            {"x": 82.0, "y": 54.6, "grow": 205},
            {"x": 80.0, "y": 55.4, "grow": 195},
        ],
    },
}


def main() -> int:
    out_dir = PROJECT / "assets" / "arche3b"
    rendered = render_overlays([MAP], out_dir, overwrite=True)
    if not rendered:
        print("рендер упал"); return 1

    manifest = PROJECT / "overlays_rendered.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    by_id = {o["id"]: o for o in data["overlays"]}
    by_id["arch_i2"] = rendered[0]  # обновлённый file-путь
    data["overlays"] = sorted(by_id.values(), key=lambda o: o["start"])
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    seq = pymiere.objects.app.project.activeSequence
    v8 = seq.videoTracks[7]
    removed = 0
    for c in reversed(list(v8.clips)):
        if 389.0 <= c.start.seconds <= 391.0:
            c.remove(False, False); removed += 1
    print(f"старый arch_i2 снят: {removed}")

    n = place_overlays(seq, rendered, PROJECT.resolve(), track_idx=7)
    pymiere.objects.app.project.save()
    print(f"уложено {n}, сохранено")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
