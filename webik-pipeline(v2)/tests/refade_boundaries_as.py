"""Перекладывает dip-to-black фейды на ЖИВОМ таймлайне: убирает фейд с КАЖДОГО клипа V3
(резкие склейки внутри темы) и оставляет фейд ТОЛЬКО на стыках тем — первый кадр темы
приходит из фейда, последний уходит в фейд. Переиспользует исправленный build_scene_plan
+ apply_fades_batch_es из assemble_as (там та же граничная логика уже зашита).

Premiere с нужным проектом должен быть ОТКРЫТ. Запуск:
  ../webik-pipeline/.venv/Scripts/python.exe tests/refade_boundaries_as.py
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import tests.assemble_as as A  # noqa: E402


def main() -> int:
    scenes = json.loads(A.SCENES_PATH.read_text(encoding="utf-8"))["scenes"]
    alignment = json.loads(A.ALIGNMENT_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(A.MANIFEST_PATH.read_text(encoding="utf-8"))

    plan = A.build_scene_plan(scenes, alignment["scenes"], float(alignment["duration"]), manifest)
    body = [e for e in plan if not e["is_card"]]
    specs = [{"start": e["start"], "fi": e["fade_in"], "fo": e["fade_out"]} for e in body]
    n_fade = sum(1 for e in body if e["fade_in"] > 0 or e["fade_out"] > 0)
    print(f"клипов V3: {len(body)} | с фейдом (стыки тем): {n_fade} | резких склеек: {len(body)-n_fade}", flush=True)

    r = A.apply_fades_batch_es(A.PARALLAX_VIDEO_TRACK_IDX, specs)
    print(f"apply: {r}", flush=True)

    A.save_project()
    print("проект сохранён", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
