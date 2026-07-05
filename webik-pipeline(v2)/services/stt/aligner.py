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
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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


def _build_exp_to_whisper_map(
    exp_norm: List[str], wh_norm: List[str]
) -> List[Optional[int]]:
    """Сопоставление exp_idx → whisper_idx через difflib opcodes.

    Устойчиво к insertions/deletions Whisper'а: лишние слова whisper'а
    пропускаются (insert), отсутствующие в whisper'е остаются None (delete),
    замены распределяются пропорционально (replace).
    """
    n = len(exp_norm)
    mapping: List[Optional[int]] = [None] * n
    matcher = SequenceMatcher(a=exp_norm, b=wh_norm, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for offset in range(i2 - i1):
                mapping[i1 + offset] = j1 + offset
        elif tag == "replace":
            exp_len = i2 - i1
            wh_len = j2 - j1
            if wh_len > 0:
                for k in range(exp_len):
                    j = j1 + min(wh_len - 1, int(k * wh_len / max(1, exp_len)))
                    mapping[i1 + k] = j
        # 'delete' (в exp но не в wh) → оставляем None
        # 'insert' (в wh но не в exp) → нет exp_idx чтобы маппить
    return mapping


def _map_scenes_to_whisper_words(
    scenes: List[Dict], whisper_words: List[Dict]
) -> Dict[str, Dict]:
    """Сопоставляет каждую сцену с диапазоном слов из whisper-вывода
    через лексический anchor-mapping (difflib SequenceMatcher).

    Раньше использовался курсор: брали ровно N слов whisper'а на сцену.
    При любом insert/delete от Whisper'а это давало каскадный drift —
    границы сцен ползли на 1-2 слова в каждой следующей сцене.

    Теперь: собираем плоский expected по всем сценам, строим mapping
    exp_idx → whisper_idx через opcodes, и для каждой сцены берём
    timestamps первого и последнего РЕАЛЬНО замапленного слова в её диапазоне.

    Returns:
        {scene_id: {"start": float, "end": float, "n_words": int,
                    "expected": [str], "actual": [str], "match_rate": float}}
    """
    # 1) Плоский expected и индексы границ каждой сцены
    all_expected: List[str] = []
    scene_ranges: List[Tuple[str, int, int, List[str]]] = []
    for s in scenes:
        sid = s["id"]
        raw = split_to_words(s.get("voiceover", ""))
        start = len(all_expected)
        all_expected.extend(raw)
        end = len(all_expected)
        scene_ranges.append((sid, start, end, raw))

    if not whisper_words or not all_expected:
        timings: Dict[str, Dict] = {}
        for sid, _, _, raw in scene_ranges:
            timings[sid] = {
                "start": 0.0, "end": 0.0, "n_words": len(raw),
                "expected": raw, "actual": [], "match_rate": 0.0,
            }
        return timings

    # 2) Нормализованные списки для матча
    exp_norm = [_normalize_word(w) for w in all_expected]
    wh_norm = [_normalize_word(w["word"]) for w in whisper_words]

    # 3) Mapping exp_idx → whisper_idx
    mapping = _build_exp_to_whisper_map(exp_norm, wh_norm)

    # 4) Per-scene таймкоды по первому и последнему замапленному слову
    timings: Dict[str, Dict] = {}
    for sid, start_idx, end_idx, raw in scene_ranges:
        if start_idx == end_idx:
            timings[sid] = {"start": 0.0, "end": 0.0, "n_words": 0,
                            "expected": [], "actual": []}
            continue

        first_wh = next(
            (mapping[i] for i in range(start_idx, end_idx) if mapping[i] is not None),
            None,
        )
        last_wh = next(
            (mapping[i] for i in range(end_idx - 1, start_idx - 1, -1) if mapping[i] is not None),
            None,
        )

        if first_wh is None or last_wh is None:
            log.warning(f"  {sid}: не нашёл whisper-якоря, помечаю missing")
            timings[sid] = {
                "start": 0.0, "end": 0.0, "n_words": end_idx - start_idx,
                "expected": raw, "actual": [], "missing": True,
            }
            continue

        actual = [whisper_words[i]["word"] for i in range(first_wh, last_wh + 1)]
        matched = sum(1 for i in range(start_idx, end_idx) if mapping[i] is not None)
        total_exp = end_idx - start_idx
        match_rate = matched / max(1, total_exp)
        if match_rate < 0.5:
            log.warning(
                f"  {sid}: low match {matched}/{total_exp}. "
                f"Expected: {' '.join(raw[:6])}... Actual: {' '.join(actual[:6])}..."
            )

        timings[sid] = {
            "start": whisper_words[first_wh]["start"],
            "end": whisper_words[last_wh]["end"],
            "n_words": total_exp,
            "expected": raw,
            "actual": actual,
            "match_rate": round(match_rate, 2),
        }

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
