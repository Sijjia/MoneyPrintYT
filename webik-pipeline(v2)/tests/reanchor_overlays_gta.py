"""Пере-привязка оверлеев к НОВОМУ alignment (после пере-озвуча) + чистка V8 (куда их положила
сборка по старым таймкодам) + перекладка на V7 по корректным временам. Тот же контент, новое время.
  ../webik-pipeline/.venv/Scripts/python.exe tests/reanchor_overlays_gta.py"""
import json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
from pymiere.wrappers import time_from_seconds
from services.premiere_template.timeline_ops import import_media, _throttle

PROJECT = ROOT / "projects" / "2026-09-06_aysberg-gta-temnaya-storona-realnye-dela-vnutriigrovye-tayny"
V7, V8 = 6, 7


def _bespoke_scene_ids():
    """Сцены, накрытые графикой (records — вся тема; bigfoot/ufo/kurtaj — только короткие
    открывашки) — туда оверлеи НЕ кладём. Остальные сцены тем вернулись на футаж → оверлеи ок."""
    ids = set(f"scene_{n:03d}" for n in range(8, 13))          # records — вся первая тема
    ids.update(["scene_013", "scene_014", "scene_062", "scene_063", "scene_160", "scene_161"])  # короткие интро
    return ids


def main() -> int:
    data = json.loads((PROJECT / "overlays_rendered.json").read_text(encoding="utf-8"))
    overlays = data["overlays"]
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    skip = _bespoke_scene_ids()
    overlays = [o for o in overlays if o.get("scene_id") not in skip]
    print(f"оверлеев после отсева bespoke-сцен: {len(overlays)}/{len(data['overlays'])}", flush=True)
    # пере-привязка: start = старт сцены в НОВОМ alignment
    fixed = 0
    for o in overlays:
        sid = o.get("scene_id")
        if sid in al:
            o["start"] = round(al[sid]["start"] + 0.15, 2)
            fixed += 1
    (PROJECT / "overlays_rendered.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"пере-привязано: {fixed}/{len(overlays)}", flush=True)

    seq = pymiere.objects.app.project.activeSequence
    # чистим V8 (сборка положила туда по старым временам) и V7 (на всякий)
    for idx in (V8, V7):
        v = seq.videoTracks[idx]
        old = list(v.clips)
        for c in reversed(old):
            c.remove(False, False)
        print(f"V{idx+1}: очищено {len(old)}", flush=True)

    v7 = seq.videoTracks[V7]
    placed = 0
    for o in overlays:
        raw = Path(o.get("file", ""))
        cands = [raw] if raw.is_absolute() else [Path.cwd() / raw, PROJECT / raw,
                                                 PROJECT / "assets" / "overlays" / f"{o['id']}.mov"]
        f = next((c.resolve() for c in cands if c.exists()), None)
        if f is None:
            print(f"  ✗ {o['id']}: .mov нет"); continue
        item = import_media(f)
        if item is None:
            continue
        try:
            _throttle()
            v7.overwriteClip(item, time_from_seconds(float(o["start"])))
            placed += 1
            if placed % 10 == 0:
                print(f"  ...{placed}/{len(overlays)}", flush=True)
        except Exception as e:
            print(f"  ✗ {o['id']}: {str(e)[:40]}")

    pymiere.objects.app.project.save(); time.sleep(1.0)
    print(f"уложено {placed}/{len(overlays)} на V7, сохранено", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
