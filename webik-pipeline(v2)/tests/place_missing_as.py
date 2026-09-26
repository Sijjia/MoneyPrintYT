"""Доставляет недостающие клипы тела в гэпы V3 на ЖИВОМ таймлайне (сцены, у которых
медиа появилось уже после базовой сборки: реальный футаж хвоста + ARG-графика).
Находит гэпы (нет клипа рядом со start сцены), pretrim'ит под слот, кладёт, затем
переприменяет граничные фейды на весь V3. Premiere с проектом должен быть ОТКРЫТ.
  ../webik-pipeline/.venv/Scripts/python.exe tests/place_missing_as.py
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
import tests.assemble_as as A
from services.premiere_template.timeline_ops import import_media, place_clip, _throttle

TOL = 0.4


def main() -> int:
    scenes = json.loads((A.PROJECT_DIR / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    alignment = json.loads((A.ALIGNMENT_PATH).read_text(encoding="utf-8"))
    manifest = json.loads((A.MANIFEST_PATH).read_text(encoding="utf-8"))
    plan = A.build_scene_plan(scenes, alignment["scenes"], float(alignment["duration"]), manifest)

    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[A.PARALLAX_VIDEO_TRACK_IDX]
    existing = []
    for i in range(v3.clips.numItems):
        existing.append(v3.clips[i].start.seconds)
    existing.sort()

    def has_clip(t):
        return any(abs(t - s) < TOL for s in existing)

    body = [e for e in plan if not e["is_card"] and e["media"] is not None]
    missing = [e for e in body if not has_clip(e["start"])]
    print(f"тело: {len(body)} | на V3: {v3.clips.numItems} | недостаёт: {len(missing)}", flush=True)

    A.TRIMMED_DIR.mkdir(parents=True, exist_ok=True)
    placed = fail = 0
    for e in missing:
        src = e.get("src_for_pretrim")
        dst = e["media"]
        if src is None:
            # media уже готовый файл (parallax) — берём как есть
            src = dst
        try:
            if not Path(dst).exists() or Path(dst).stat().st_size < 20000:
                if not A.pretrim_fill(Path(src), Path(dst), e["target_dur"]):
                    print(f"  ✗ pretrim {e['id']}"); fail += 1; continue
            item = import_media(Path(dst))
            if item is None:
                print(f"  ✗ import {e['id']}"); fail += 1; continue
            _throttle(); place_clip(v3, item, e["start"]); placed += 1
            print(f"  ✓ {e['id']} @ {e['start']:.1f}s", flush=True)
        except Exception as ex:
            print(f"  ✗ {e['id']}: {str(ex)[:70]}"); fail += 1

    print(f"\nдоставлено {placed}, ошибок {fail}", flush=True)

    # переприменяем граничные фейды на весь V3 (новые клипы тоже получат фейд на стыках тем)
    specs = [{"start": e["start"], "fi": e["fade_in"], "fo": e["fade_out"]} for e in body]
    r = A.apply_fades_batch_es(A.PARALLAX_VIDEO_TRACK_IDX, specs)
    print(f"fades: {r}", flush=True)

    A.save_project()
    print("сохранено", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
