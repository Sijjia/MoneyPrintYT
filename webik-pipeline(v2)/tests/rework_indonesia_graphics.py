"""Индонезия «ниндзя» (6:29–7:46): заменяем простой кино-стат на драматичный
ShockCounter 0→307 + добавляем карту распространения линчеваний.

ВАЖНО: из-за обреза Айдара alignment сдвинут ~19.7с относительно таймлайна,
поэтому тайминги считаны по таймлайну (307 звучит ~435.7с).

Аддитивно на V8 (правки Айдара не трогаем): удаляем клип cine_02, кладём новые.
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
OVERLAY_TRACK = 7

SHOCK = {
    "id": "arch_i1",
    "type": "shock",
    "composition": "ShockCounter",
    "scene_id": "scene_079",
    "start": 432.7,   # 307 звучит ~435.7 на таймлайне; климб ~3с
    "duration_sec": 5.0,
    "anchor": "погибло около 307 человек",
    "props": {"from": 0, "to": 307, "label": "погибших", "sub": "Восточная Ява · 1998", "accent": ACCENT},
}

MAP = {
    "id": "arch_i2",
    "type": "mapspread",
    "composition": "MapSpread",
    "scene_id": "scene_076",
    "start": 390.0,
    "duration_sec": 8.0,
    "anchor": "волна массовых линчеваний по Баньюванги и Джембер",
    "props": {
        "title": "Индонезия · 1998",
        "label": "Ночная охота на «колдунов»",
        "durationInFrames": 240,
        "accent": ACCENT,
        # Восточная Ява на эквиректе world_equi.jpg
        "origins": [
            {"x": 82.0, "y": 54.6, "grow": 210, "label": "Баньюванги"},
            {"x": 79.6, "y": 55.7, "grow": 200, "label": "Джембер"},
        ],
    },
}

NEW = [MAP, SHOCK]
DROP_CINE = {"cine_02"}


def main() -> int:
    rendered = render_overlays(NEW, PROJECT / "assets" / "arche3", overwrite=True)
    if len(rendered) != len(NEW):
        print(f"ВНИМАНИЕ: отрендерено {len(rendered)}/{len(NEW)}")

    # убрать cine_02 из cine_scenes.json (чтобы place_all_graphics его не вернул)
    cs_path = PROJECT / "cine_scenes.json"
    cs = json.loads(cs_path.read_text(encoding="utf-8"))
    before = len(cs["scenes"])
    cs["scenes"] = [c for c in cs["scenes"] if c.get("id") not in DROP_CINE]
    cs_path.write_text(json.dumps(cs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"cine_scenes: убрано {before - len(cs['scenes'])} ({DROP_CINE})")

    # домерж новых в overlays_rendered.json
    manifest = PROJECT / "overlays_rendered.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    by_id = {o["id"]: o for o in data["overlays"]}
    for r in rendered:
        by_id[r["id"]] = r
    data["overlays"] = sorted(by_id.values(), key=lambda o: o["start"])
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    seq = pymiere.objects.app.project.activeSequence
    v8 = seq.videoTracks[OVERLAY_TRACK]
    # удалить клип cine_02 (start ~433.17)
    removed = 0
    for c in reversed(list(v8.clips)):
        if 432.0 <= c.start.seconds <= 434.5 and "cine_02" in c.name:
            c.remove(False, False)
            removed += 1
    print(f"V8: удалён cine_02 клип: {removed}")

    n = place_overlays(seq, rendered, PROJECT.resolve(), track_idx=OVERLAY_TRACK)
    pymiere.objects.app.project.save()
    print(f"уложено {n}, сохранено")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
