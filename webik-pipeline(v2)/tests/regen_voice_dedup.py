"""Перегенерация голоса + alignment ПОСЛЕ чистки 40 терсе-дублей из scenes.json.
Повторяет логику stage_04 (сборка voiceover со швами уровней → Voicer → whisper
alignment → нормализация пауз перед уровнями → re-align), но БЕЗ шага медиа —
manifest/медиа не трогаются. Запуск:
    PYTHONUTF8=1 ../webik-pipeline/.venv/Scripts/python.exe tests/regen_voice_dedup.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.tts.voicer import VoicerTTS, SEAM_MARKER
from services.stt.aligner import align_with_whisper, save_alignment
from stages.stage_04_assets import _insert_structured_pauses

PROJECT = Path("projects/2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-")
assets = PROJECT / "assets"
voice_path = assets / "voice" / "full.mp3"


def log(m):
    print(m, flush=True)


def main():
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    log(f"[0] сцен в чистом scenes.json: {len(scenes)}")

    # 1. Сборка единого voiceover со швами на границах уровней (как stage_04:71-88)
    parts, prev_level, n_seams = [], None, 0
    for s in scenes:
        vo = (s.get("voiceover") or "").strip()
        if not vo:
            continue
        lvl = s.get("level", 0)
        if prev_level is not None and lvl != prev_level:
            parts.append(SEAM_MARKER)
            n_seams += 1
        parts.append(vo)
        prev_level = lvl
    full_text = " ".join(parts)
    n_chars = len(full_text)
    n_words = len(full_text.replace(SEAM_MARKER, " ").split())
    log(f"[1] voiceover собран: {len(parts)} сегментов, {n_seams} швов, "
        f"{n_words} слов, {n_chars} символов")
    if not full_text.replace(SEAM_MARKER, "").strip():
        log("ПУСТО — abort")
        sys.exit(1)

    # 2. Синтез (перезапись full.mp3)
    if voice_path.exists():
        voice_path.unlink()
        log("[2] старый full.mp3 удалён")
    log("[2] синтез голоса через Voicer (тот же шаблон)...")
    VoicerTTS().synthesize(full_text, voice_path)
    log(f"[2] готово: {voice_path.name} = {voice_path.stat().st_size // 1024} KB")

    # 3. Whisper alignment
    log("[3] whisper alignment...")
    alignment = align_with_whisper(scenes, voice_path)
    log(f"[3] alignment: duration={alignment.get('duration'):.1f}s, "
        f"scenes={len(alignment.get('scenes', []))}")

    # 3b. Нормализация пауз перед уровнями + re-align (как stage_04:110-119)
    if not bool(alignment.get("paused_at_levels")):
        if _insert_structured_pauses(voice_path, scenes, alignment, default_pause_sec=1.5):
            log("[3b] нормализованы паузы перед уровнями, re-run whisper alignment")
            alignment = align_with_whisper(scenes, voice_path)
        alignment["paused_at_levels"] = True

    save_alignment(alignment, assets / "alignment.json")
    log(f"[4] alignment.json сохранён. duration={alignment.get('duration'):.1f}s")

    # 4. Быстрый health-check: сколько сцен НЕ привязано (missing/start=0)
    asc = {s["id"]: s for s in alignment["scenes"]} if isinstance(alignment["scenes"], list) else alignment["scenes"]
    missing = [i for i, a in asc.items() if a.get("missing") or a.get("start") in (None, 0.0)]
    log(f"[5] непривязанных сцен: {len(missing)} {missing[:12]}")
    log("DONE")


if __name__ == "__main__":
    main()
