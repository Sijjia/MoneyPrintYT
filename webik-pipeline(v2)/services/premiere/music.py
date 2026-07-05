"""
services/premiere/music.py
Размещение фоновой музыки на A2 из NCS-папки пользователя.

Что делает:
- Mood-based выбор трека по preset (MYSTIC/CIPHER/SHADOW/...)
- Music на A2 от 0 до total_dur
- Fade-in 1s в начале, fade-out 2s в конце через Volume.Level keyframes
- Постоянный low volume (≈ -20 dB) между fade'ами

Что не делает (позже):
- Ducking под voice (whisper sentences) → -22 dB во время голоса
- Beat detection для cut-on-beat
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

log = setup_logger("music")

# Linear factor для Premiere audio level. 1.0 = 0 dB, 0.5 ≈ -6 dB, 0.25 ≈ -12 dB.
# 0.10 ≈ -20 dB — фоном, не перебивает голос.
MUSIC_VOLUME_FACTOR = 0.10
MUSIC_FADE_IN_SEC = 1.0
MUSIC_FADE_OUT_SEC = 2.0

# Mood-mapping пресета на ключевые слова в имени NCS-трека.
# При выборе трека сначала фильтруем по этим ключам, если ничего не найдено — берём любой.
PRESET_TRACK_KEYWORDS: Dict[str, List[str]] = {
    "MYSTIC": ["spookster", "sinister", "illusions", "just breathing", "faultlines", "rising wave"],
    "ARCHIVE": ["culture", "rising wave", "faultlines", "brass orchid"],
    "CIPHER": ["warzone", "never surrender", "sinister", "illusions"],
    "COSMIC": ["rising wave", "chasing the dragons", "brass orchid", "just breathing"],
    "SHADOW": ["warzone", "never surrender", "sinister", "spookster"],
}


def find_ncs_tracks(music_dir: Optional[Path]) -> List[Path]:
    if not music_dir:
        return []
    p = Path(music_dir)
    if not p.exists() or not p.is_dir():
        return []
    return sorted(
        f for f in p.iterdir()
        if f.is_file() and f.suffix.lower() in (".mp3", ".wav", ".m4a", ".flac")
    )


def _filter_by_preset(tracks: List[Path], preset: Optional[str]) -> List[Path]:
    """Возвращает подмножество треков чьи имена содержат preset-ключи.
    Если ничего не подходит или preset неизвестен — возвращает все треки."""
    if not preset:
        return tracks
    keys = PRESET_TRACK_KEYWORDS.get(preset.upper())
    if not keys:
        return tracks
    filtered = [t for t in tracks if any(k.lower() in t.name.lower() for k in keys)]
    return filtered or tracks


def place_music(
    sequence,
    total_dur_sec: float,
    music_dir: Optional[Path],
    seed: Optional[int] = None,
    preset: Optional[str] = None,
) -> Optional[str]:
    """Кладёт mood-подобранный NCS-трек на A2 от 0 до total_dur_sec с fade-in/out.

    Args:
        preset: имя пресета (MYSTIC/ARCHIVE/CIPHER/COSMIC/SHADOW) для mood-mapping.
            Фильтрует треки по PRESET_TRACK_KEYWORDS. Если None — выбираем из всех.

    Returns:
        Имя выбранного трека, либо None если папка пустая или ошибка.
    """
    tracks = find_ncs_tracks(music_dir)
    if not tracks:
        log.info(f"NCS треков не найдено в {music_dir}")
        return None

    candidates = _filter_by_preset(tracks, preset)
    log.info(
        f"Найдено {len(tracks)} NCS треков, после фильтра по preset='{preset}': {len(candidates)}"
    )

    audio_tracks = sequence.audioTracks
    if audio_tracks.numTracks < 2:
        log.warning(f"A2 нет в sequence ({audio_tracks.numTracks} audio tracks) — музыку не положу")
        return None
    a2 = audio_tracks[1]

    rng = random.Random(seed)
    picked = rng.choice(candidates)
    log.info(f"Выбран трек: {picked.name}")

    items = import_files([picked])
    if not items:
        log.warning(f"Не смог импортировать {picked.name}")
        return None
    music_item = items[0]

    try:
        a2.insertClip(music_item, time_from_seconds(0.0))
    except Exception as e:
        log.warning(f"A2.insertClip music упал: {e}")
        return None

    clip = find_clip_by_timeline_start(a2, 0.0)
    if clip is None:
        log.warning("Не нашёл вставленный music clip на A2")
        return None

    try:
        clip.end = time_from_seconds(total_dur_sec)
    except Exception as e:
        log.warning(f"Не смог trim music до {total_dur_sec:.2f}s: {e}")

    # Volume keyframes: fade-in + flat + fade-out
    _apply_volume_envelope(clip, total_dur_sec, MUSIC_VOLUME_FACTOR, MUSIC_FADE_IN_SEC, MUSIC_FADE_OUT_SEC)

    log.info(
        f"  A2: '{picked.stem}' 0.00s→{total_dur_sec:.2f}s, "
        f"volume={MUSIC_VOLUME_FACTOR:.2f}, fade_in={MUSIC_FADE_IN_SEC}s, fade_out={MUSIC_FADE_OUT_SEC}s"
    )
    return picked.name


def _apply_volume_envelope(
    clip,
    total_dur_sec: float,
    flat_level: float,
    fade_in_sec: float,
    fade_out_sec: float,
):
    """Volume keyframes: 0 → flat_level (fade_in_sec) → flat_level → 0 (fade_out_sec)."""
    volume_comp = _find_component(clip, "Volume")
    if volume_comp is None:
        log.warning("Volume компонент не найден на music clip")
        return

    level_prop = _find_property(volume_comp, "Level")
    if level_prop is None:
        log.warning("Level property не найдена в Volume component")
        return

    if not level_prop.areKeyframesSupported():
        log.warning("Volume.Level не поддерживает keyframes — устанавливаю константу")
        try:
            level_prop.setValue(float(flat_level), True)
        except Exception as e:
            log.warning(f"Volume.Level.setValue failed: {e}")
        return

    if not level_prop.isTimeVarying():
        level_prop.setTimeVarying(True)

    in_sec = clip.inPoint.seconds
    out_sec = clip.outPoint.seconds
    clip_dur = out_sec - in_sec
    fi = min(fade_in_sec, clip_dur / 4.0)
    fo = min(fade_out_sec, clip_dur / 4.0)

    try:
        level_prop.removeKeyRange(in_sec, out_sec, True)
    except Exception:
        pass

    try:
        # Fade-in: 0 → flat_level за fi сек
        level_prop.addKey(in_sec)
        level_prop.setValueAtKey(in_sec, 0.0, True)
        level_prop.addKey(in_sec + fi)
        level_prop.setValueAtKey(in_sec + fi, float(flat_level), True)
        # Hold flat
        level_prop.addKey(out_sec - fo)
        level_prop.setValueAtKey(out_sec - fo, float(flat_level), True)
        # Fade-out: flat_level → 0
        level_prop.addKey(out_sec)
        level_prop.setValueAtKey(out_sec, 0.0, True)
    except Exception as e:
        log.warning(f"Volume keyframes setValue failed: {e}")


def _try_set_audio_level_legacy(clip, level_factor: float):
    """Установить постоянный audio level через Volume → Level property.

    В Premiere audio level — linear factor [0, ~16] (0=mute, 1=0 dB, 2=+6 dB).
    """
    volume_comp = _find_component(clip, "Volume")
    if volume_comp is None:
        # На audio clip компонент может называться иначе
        for alt in ["Audio", "Channel Volume", "Output Volume"]:
            volume_comp = _find_component(clip, alt)
            if volume_comp is not None:
                break
    if volume_comp is None:
        log.warning("Volume компонент не найден на music clip")
        return

    level_prop = _find_property(volume_comp, "Level")
    if level_prop is None:
        for alt in ["Bypass", "Volume", "Output"]:
            level_prop = _find_property(volume_comp, alt)
            if level_prop is not None and "level" in alt.lower() or alt.lower() == "volume":
                break
    if level_prop is None:
        log.warning("Level property не найдена в Volume component")
        return

    try:
        level_prop.setValue(float(level_factor), True)
    except Exception as e:
        log.warning(f"Volume.Level.setValue({level_factor}) упал: {e}")
