"""Ставит отрендеренное интро на V3 вместо стоков scene_001..004.

Интро (remotion IntroFootage) уже синхронизировано по словам из assets/alignment.json
и само содержит всю графику первых 55 секунд, поэтому старые кино-оверлеи V8,
попадающие в эту зону, снимаются — иначе они лягут поверх интро.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pymiere
from pymiere.wrappers import time_from_seconds

from services.premiere.effects import apply_dip_to_black_fade, find_clip_by_timeline_start, mute_linked_audio
from services.premiere_template.media_swap import ensure_premiere_open
from services.premiere_template.timeline_ops import clear_zone_es, import_media

PROJECT_DIR = (Path(__file__).resolve().parent.parent / "projects"
               / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-")
PRPROJ = PROJECT_DIR / "project_template.prproj"
INTRO_DIR = PROJECT_DIR / "assets" / "intro"
# Premiere держит уже импортированный файл — каждый новый рендер кладём под новым именем,
# берём самый свежий
_variants = sorted(INTRO_DIR.glob("intro_*.mov"), key=lambda p: p.stat().st_mtime)
INTRO = _variants[-1] if _variants else INTRO_DIR / "intro_main.mov"

BODY_TRACK = 2      # V3 — основной видеослой
OVERLAY_TRACK = 7   # V8 — кино-оверлеи
OVERLAY_AUDIO = 10  # A11 — связанный звук оверлеев

INTRO_END = 58.40   # до карточки уровня (scene_005 @58.52)
ZONE = 58.0


def main() -> int:
    if not INTRO.exists():
        print(f"нет файла интро: {INTRO}")
        return 1
    ensure_premiere_open(PRPROJ)
    seq = pymiere.objects.app.project.activeSequence
    print(f"секвенция: {seq.name}")

    print(f"[1] снимаем старые клипы из зоны 0-{ZONE:.0f}с")
    for kind, idx, label in (("videoTracks", BODY_TRACK, "V3"),
                             ("videoTracks", OVERLAY_TRACK, "V8"),
                             ("audioTracks", OVERLAY_AUDIO, "A11")):
        print(f"    {label}: снято {clear_zone_es(kind, idx, ZONE)}")

    print("[2] импорт интро")
    item = import_media(INTRO)
    if item is None:
        print("не удалось импортировать интро")
        return 1

    print("[3] укладка на V3 @ 0.00")
    v3 = seq.videoTracks[BODY_TRACK]
    v3.overwriteClip(item, time_from_seconds(0.0))
    clip = find_clip_by_timeline_start(v3, 0.0)
    if clip is None:
        print("клип не найден после укладки")
        return 1
    if clip.end.seconds > INTRO_END + 0.05:
        clip.end = time_from_seconds(INTRO_END)
    mute_linked_audio(clip)
    # проявление уже внутри самого интро — гасим только хвост перед карточкой уровня
    apply_dip_to_black_fade(clip, fade_in_sec=0.0, fade_out_sec=0.4, do_fade_in=False, do_fade_out=True)
    print(f"    интро 0.00-{clip.end.seconds:.2f}")

    pymiere.objects.app.project.save()
    print("проект сохранён")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
