"""Ставит анимационную вставку на scene_011 (V7) и делает ПЛАВНЫЙ ПЕРЕХОД в
следующую анимацию cine_01 (V8): вставка угасает (fade-out), cine_01 проявляется
(fade-in) — кроссдиссолв на стыке. Тело V3 не трогаем.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pymiere
from pymiere.wrappers import time_from_seconds
from services.premiere_template.timeline_ops import import_media
from tests.assemble_iceberg_test import apply_dip_to_black_fade

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-"
OUT = (PROJECT / "assets" / "v7_inserts").resolve()
INS_START = 93.9      # начало scene_011
XFADE = 1.0           # длительность кроссдиссолва


def main() -> int:
    mov = OUT / "v7_scene_011_93.mov"
    if not (mov.exists() and mov.stat().st_size > 5000):
        print("нет клипа v7_scene_011_93.mov"); return 1
    seq = pymiere.objects.app.project.activeSequence
    v7 = seq.videoTracks[6]; v8 = seq.videoTracks[7]

    # 1) поставить вставку на V7
    item = import_media(mov)
    if item is None:
        print("import упал"); return 1
    v7.overwriteClip(item, time_from_seconds(round(INS_START, 2)))
    # найти только что поставленный клип на V7 (по началу)
    ins = None
    for i in range(v7.clips.numItems):
        c = v7.clips[i]
        if abs(c.start.seconds - INS_START) < 0.4:
            ins = c; break
    if ins is None:
        print("не нашёл вставку на V7"); return 1
    # fade-out в конце (уходит в cine_01)
    apply_dip_to_black_fade(ins, 0.0, XFADE)
    ins_end = ins.end.seconds
    print(f"вставка V7: {ins.start.seconds:.1f}-{ins_end:.1f}, fade-out {XFADE}с")

    # 2) cine_01 на V8 — fade-in в начале (проявляется навстречу)
    cine = None
    for i in range(v8.clips.numItems):
        c = v8.clips[i]
        try: n = Path(c.projectItem.getMediaPath()).name.lower()
        except Exception: n = c.name.lower()
        if "cine_01" in n:
            cine = c; break
    if cine is not None:
        apply_dip_to_black_fade(cine, XFADE, 0.0)
        print(f"cine_01: {cine.start.seconds:.1f}-{cine.end.seconds:.1f}, fade-in {XFADE}с (кроссдиссолв)")
    else:
        print("cine_01 не найден на V8 — переход только по fade-out вставки")

    # записать в v7_inserts.json для учёта
    p = PROJECT / "v7_inserts.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    d["inserts"] = [c for c in d["inserts"] if c.get("scene_id") != "scene_011"]
    d["inserts"].append({"scene_id": "scene_011", "start": INS_START, "end": round(ins_end, 2),
                         "dur": round(ins_end - INS_START, 2), "source": "cartoon",
                         "title": "DuckTales", "idea": "жадность/деньги, переход в cine_01"})
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

    pymiere.objects.app.project.save()
    print("готово, проект сохранён")
    return 0


if __name__ == "__main__":
    sys.exit(main())
