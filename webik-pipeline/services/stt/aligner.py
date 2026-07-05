"""
services/stt/aligner.py
Force-alignment текста к аудио и сопоставление сцен с реальными таймстампами.

Два способа alignment:
- align_with_whisper(scenes, audio) — точный (faster-whisper, word-level ±50мс).
- align_proportional(text, audio) — fallback, распределяет слова пропорционально
  длительности; ±пол-секунды, но не требует whisper-модели.

Stage 4 предпочитает whisper и падает на proportional только если whisper
недоступен (нет модели или ошибка загрузки).
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

import ffmpeg

from core.logger import setup_logger

log = setup_logger("aligner")


def get_audio_duration(audio_path: Path) -> float:
    """Длительность аудио в секундах через ffprobe."""
    probe = ffmpeg.probe(str(audio_path))
    return float(probe["format"]["duration"])


def split_to_words(text: str) -> List[str]:
    """Разбивает текст на слова, сохраняя пунктуацию приклеенной к слову."""
    cleaned = re.sub(r"<break[^>]*/>", "", text)
    cleaned = re.sub(r"\[пауза[^\]]*\]", "", cleaned)
    tokens = re.findall(r"\S+", cleaned)
    return tokens


def split_to_sentences(text: str) -> List[str]:
    cleaned = re.sub(r"<break[^>]*/>", "", text)
    cleaned = re.sub(r"\[пауза[^\]]*\]", "", cleaned)
    parts = re.split(r"(?<=[.!?])\s+", cleaned.strip())
    return [p for p in parts if p]


def _normalize_word(w: str) -> str:
    return re.sub(r"[^\w]+", "", w.lower(), flags=re.UNICODE)


def _map_scenes_to_whisper_words(
    scenes: List[Dict], whisper_words: List[Dict]
) -> Dict[str, Dict]:
    """Сопоставляет каждую сцену с диапазоном слов из whisper-вывода.

    Идём по сценам последовательно: для каждой берём столько whisper-слов,
    сколько слов в её voiceover, и фиксируем start/end по реальным
    таймстампам whisper. Логируем mismatch если нормализованные слова
    сильно расходятся (whisper мог что-то ослышать или объединить).

    Returns:
        {scene_id: {"start": float, "end": float, "n_words": int,
                    "expected": [str], "actual": [str]}}
    """
    timings: Dict[str, Dict] = {}
    cursor = 0
    total = len(whisper_words)

    for scene in scenes:
        sid = scene["id"]
        voiceover = scene.get("voiceover", "")
        expected = split_to_words(voiceover)
        n = len(expected)

        if n == 0:
            t = whisper_words[cursor]["start"] if cursor < total else 0.0
            timings[sid] = {"start": t, "end": t, "n_words": 0, "expected": [], "actual": []}
            continue

        if cursor >= total:
            log.warning(f"  {sid}: whisper кончился, осталось {n} слов без таймстампов")
            last_t = whisper_words[-1]["end"] if total else 0.0
            timings[sid] = {
                "start": last_t,
                "end": last_t,
                "n_words": n,
                "expected": expected,
                "actual": [],
                "missing": True,
            }
            continue

        start_idx = cursor
        end_idx = min(cursor + n - 1, total - 1)
        actual = [whisper_words[i]["word"] for i in range(start_idx, end_idx + 1)]

        # Mismatch detection — без жёсткой ошибки, просто warning
        exp_norm = [_normalize_word(w) for w in expected]
        act_norm = [_normalize_word(w) for w in actual]
        matches = sum(1 for e, a in zip(exp_norm, act_norm) if e == a)
        match_rate = matches / max(1, len(exp_norm))
        if match_rate < 0.5:
            log.warning(
                f"  {sid}: whisper расслышал по-другому ({matches}/{len(exp_norm)} совпадений). "
                f"Expected: {' '.join(expected[:8])}... Actual: {' '.join(actual[:8])}..."
            )

        timings[sid] = {
            "start": whisper_words[start_idx]["start"],
            "end": whisper_words[end_idx]["end"],
            "n_words": n,
            "expected": expected,
            "actual": actual,
            "match_rate": round(match_rate, 2),
        }
        cursor += n

    return timings


def align_with_whisper(scenes: List[Dict], audio_path: Path) -> Dict:
    """Точный alignment через faster-whisper.

    Returns тот же формат что и align_proportional, плюс:
        - "method": "whisper"
        - "scenes": {scene_id: {start, end, n_words, expected, actual}}
    """
    from services.stt.whisper import WhisperAligner

    aligner = WhisperAligner()
    whisper_result = aligner.transcribe(audio_path)

    scene_timings = _map_scenes_to_whisper_words(scenes, whisper_result["words"])

    return {
        "duration": whisper_result["duration"],
        "method": "whisper",
        "language": whisper_result["language"],
        "words": whisper_result["words"],
        "sentences": whisper_result["segments"],
        "scenes": scene_timings,
    }


def align_proportional(text: str, audio_path: Path) -> Dict:
    """Распределяет слова и предложения равномерно по длительности аудио.

    Используется как fallback если faster-whisper недоступен.
    """
    duration = get_audio_duration(audio_path)
    words = split_to_words(text)
    sentences = split_to_sentences(text)

    if not words:
        return {
            "duration": duration,
            "method": "proportional",
            "words": [],
            "sentences": [],
        }

    weights = [max(1, len(w)) for w in words]
    total_w = sum(weights)
    word_durations = [duration * w / total_w for w in weights]

    word_entries = []
    t = 0.0
    for word, dur in zip(words, word_durations):
        word_entries.append({"word": word, "start": round(t, 3), "end": round(t + dur, 3)})
        t += dur

    sentence_entries = []
    cursor = 0
    for sent in sentences:
        sent_words = split_to_words(sent)
        n = len(sent_words)
        if cursor + n > len(word_entries):
            n = len(word_entries) - cursor
        if n <= 0:
            break
        start = word_entries[cursor]["start"]
        end = word_entries[cursor + n - 1]["end"]
        sentence_entries.append({"text": sent, "start": start, "end": end})
        cursor += n

    return {
        "duration": round(duration, 3),
        "method": "proportional",
        "words": word_entries,
        "sentences": sentence_entries,
    }


def proportional_scene_timings(scenes: List[Dict], total_duration: float) -> Dict[str, Dict]:
    """Распределение сцен пропорционально по словам в их voiceover.

    Используется как fallback вместе с align_proportional.
    """
    weights = []
    word_lists = []
    for scene in scenes:
        ws = split_to_words(scene.get("voiceover", ""))
        word_lists.append(ws)
        weights.append(max(1, sum(len(w) for w in ws)) if ws else 1)
    total_w = sum(weights)

    timings: Dict[str, Dict] = {}
    cursor_t = 0.0
    for scene, ws, w in zip(scenes, word_lists, weights):
        dur = total_duration * w / total_w
        timings[scene["id"]] = {
            "start": round(cursor_t, 3),
            "end": round(cursor_t + dur, 3),
            "n_words": len(ws),
            "expected": ws,
            "actual": [],
        }
        cursor_t += dur
    return timings


def save_alignment(alignment: Dict, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(alignment, ensure_ascii=False, indent=2), encoding="utf-8")
    method = alignment.get("method", "?")
    log.info(
        f"Alignment ({method}) → {out_path} "
        f"({len(alignment.get('words', []))} слов, "
        f"{len(alignment.get('scenes', {}))} сцен)"
    )
    return out_path
