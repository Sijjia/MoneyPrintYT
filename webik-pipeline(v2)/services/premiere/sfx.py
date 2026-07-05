"""
services/premiere/sfx.py
Точечная расстановка SFX на A3 по trigger_word из scenes[i].sfx[].

Каждый SFX-entry в scenes.json:
    {"type": "bass_drop", "trigger_word": "исчезновением", "intensity": 0.8}

Алгоритм:
1. Найти trigger_word в whisper-words alignment.json — получить точный timestamp начала слова.
2. По type определить категорию папки в Old Sport SFX Pack.
3. Опционально отфильтровать по sub-keyword (bass_drop → "импакт"/"разгон").
4. Случайный файл из подходящих, импорт в проект, insertClip на A3 в timestamp.

Категории:
- bass_drop / impact / revealer → Разгоны+удары
- whoosh                       → Для Переходов (вуши)
- appear                       → Для появления (вуши)
- glitch                       → Глитчи
- paper                        → Бумага
- marker                       → Маркер
- notification / error         → Интерфейсы
- keyboard                     → Клавиатура - мышь
- camera_click                 → Фото - щелчки
"""
import random
from pathlib import Path
from typing import Dict, List, Optional

from pymiere.wrappers import time_from_seconds

from core.logger import setup_logger
from services.premiere.effects import (
    _find_component,
    _find_property,
    find_clip_by_timeline_start,
)
from services.premiere.pymiere_wrapper import import_files
from services.stt.aligner import _normalize_word

log = setup_logger("sfx")

# Linear factor для Premiere audio Volume.Level. 1.0 = 0 dB.
# Default 0.18 ≈ -15 dB — слышимый акцент, не глушит голос. Multiplied на intensity (default 1.0).
# При intensity=0.8 → итог 0.144 ≈ -17 dB (Webik-style тонкий sound design).
SFX_DEFAULT_VOLUME = 0.18

SFX_TYPE_TO_CATEGORY: Dict[str, str] = {
    "bass_drop": "Разгоны+удары",
    "impact": "Разгоны+удары",
    "revealer": "Разгоны+удары",
    "whoosh": "Для Переходов (вуши)",
    "appear": "Для появления (вуши)",
    "glitch": "Глитчи",
    "paper": "Бумага",
    "marker": "Маркер",
    "notification": "Интерфейсы",
    "error": "Интерфейсы",
    "keyboard": "Клавиатура - мышь",
    "camera_click": "Фото - щелчки",
}

# Дополнительные ключи для уточнения внутри категории.
# Из «Разгоны+удары» для bass_drop хочется именно Импакт (короткий ударный),
# а не Разгон (длинный нарастающий) — выбираем по совпадению слов в имени файла.
SFX_TYPE_KEYWORDS: Dict[str, List[str]] = {
    "bass_drop": ["импакт"],
    "impact": ["импакт"],
    "revealer": ["ревилер"],
    "appear": ["короткий"],
    "notification": ["уведомление"],
    "error": ["еррор"],
}

# Исключающие ключи: если имя файла содержит — выкидываем из выборки.
# Для bass_drop колокольчик звучит звонко, не как глухой удар — отсеиваем.
SFX_TYPE_EXCLUDE_KEYWORDS: Dict[str, List[str]] = {
    "bass_drop": ["колокольчик"],
}


def find_sfx_for_type(sfx_type: str, sfx_dir: Path) -> List[Path]:
    """Возвращает .wav/.mp3 файлы в подкатегории, отфильтрованные по type-keywords.

    Если ни один файл не подошёл по keyword — возвращает все файлы категории
    (лучше что-то, чем ничего).
    """
    category = SFX_TYPE_TO_CATEGORY.get(sfx_type)
    if not category:
        return []
    folder = sfx_dir / category
    if not folder.exists():
        return []
    all_files = sorted(
        f for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in (".wav", ".mp3", ".aiff", ".aif")
    )
    keywords = SFX_TYPE_KEYWORDS.get(sfx_type)
    excludes = SFX_TYPE_EXCLUDE_KEYWORDS.get(sfx_type, [])

    pool = all_files
    if keywords:
        included = [f for f in all_files if any(k in f.name.lower() for k in keywords)]
        if included:
            pool = included
    if excludes:
        pool = [f for f in pool if not any(k in f.name.lower() for k in excludes)] or pool
    return pool


def find_word_timestamp(trigger_word: str, whisper_words: List[Dict]) -> Optional[float]:
    """Ищет start time of trigger_word в whisper-words. Нормализованное сравнение
    (lowercase, без пунктуации)."""
    target = _normalize_word(trigger_word)
    if not target:
        return None
    for w in whisper_words:
        if _normalize_word(w.get("word", "")) == target:
            return float(w["start"])
    return None


def place_sfx(
    sequence,
    scenes: List[Dict],
    whisper_words: List[Dict],
    sfx_dir: Optional[Path],
    seed: Optional[int] = None,
    total_duration_sec: Optional[float] = None,
) -> int:
    """Расставляет SFX по scenes[i].sfx[] на A3.

    Returns:
        Кол-во размещённых SFX clip'ов.
    """
    if not sfx_dir or not Path(sfx_dir).exists():
        log.info(f"SFX dir не найден: {sfx_dir}")
        return 0
    if not whisper_words:
        log.info("Нет whisper-words для SFX-привязки, пропускаю")
        return 0

    # Собираем все SFX-entry заранее
    sfx_jobs = []
    for scene in scenes:
        sid = scene["id"]
        for entry in (scene.get("sfx") or []):
            sfx_type = entry.get("type")
            trigger = entry.get("trigger_word")
            if not sfx_type or not trigger:
                continue
            sfx_jobs.append((sid, sfx_type, trigger, entry.get("intensity", 1.0)))

    if not sfx_jobs:
        log.info("В scenes.json нет SFX-entry, пропускаю")
        return 0

    audio_tracks = sequence.audioTracks
    if audio_tracks.numTracks < 3:
        log.warning(
            f"A3 нет в sequence ({audio_tracks.numTracks} audio tracks) — SFX не положу"
        )
        return 0
    a3 = audio_tracks[2]

    rng = random.Random(seed)
    placed = 0

    for sid, sfx_type, trigger, intensity in sfx_jobs:
        timestamp = find_word_timestamp(trigger, whisper_words)
        if timestamp is None:
            log.warning(f"  {sid}: trigger_word '{trigger}' не найден в whisper-words")
            continue

        files = find_sfx_for_type(sfx_type, Path(sfx_dir))
        if not files:
            log.warning(f"  {sid}: type='{sfx_type}' — нет файлов в категории")
            continue

        picked = rng.choice(files)
        items = import_files([picked])
        if not items:
            log.warning(f"  {sid}: не смог импортировать {picked.name}")
            continue
        sfx_item = items[0]

        try:
            a3.insertClip(sfx_item, time_from_seconds(timestamp))
        except Exception as e:
            log.warning(f"  {sid}: A3.insertClip упал: {e}")
            continue

        # Громкость = SFX_DEFAULT_VOLUME * intensity из scenes.json (default 1.0)
        volume = SFX_DEFAULT_VOLUME * float(intensity)
        clip = find_clip_by_timeline_start(a3, timestamp)
        if clip is not None:
            _try_set_sfx_volume(clip, volume)
            # Обрезаем SFX чтобы не вылезал за конец видео (Импакт.wav 9s, контент 27s
            # → SFX до 31s типичный сценарий). Хвост SFX за границей всё равно не в экспорт,
            # но мусорит manifest и может тянуться в overlapping clips.
            if total_duration_sec is not None:
                try:
                    natural_end = clip.end.seconds
                    if natural_end > total_duration_sec:
                        clip.end = time_from_seconds(total_duration_sec)
                except Exception as e:
                    log.warning(f"  {sid}: SFX trim failed: {e}")

        placed += 1
        log.info(
            f"  A3 {sid}: '{sfx_type}' @{timestamp:.2f}s → {picked.name} "
            f"(на слове '{trigger}', volume={volume:.2f})"
        )

    return placed


def _try_set_sfx_volume(clip, level_factor: float):
    """Устанавливает Volume.Level через те же property API что music/film_burn."""
    volume_comp = _find_component(clip, "Volume")
    if volume_comp is None:
        return
    level_prop = _find_property(volume_comp, "Level")
    if level_prop is None:
        return
    try:
        level_prop.setValue(float(level_factor), True)
    except Exception as e:
        log.warning(f"SFX Volume.Level.setValue({level_factor}) упал: {e}")
