"""
services/stt/whisper.py
Word-level alignment голоса через faster-whisper (CTranslate2, без torch).

Используется в Stage 4 после генерации голоса: получаем точные start/end каждого
произнесённого слова → cuts на таймлайне ставятся синхронно с речью.
"""
from pathlib import Path
from typing import Dict, List, Optional

import ctranslate2
from faster_whisper import WhisperModel

from core.config import get_settings
from core.logger import setup_logger

log = setup_logger("whisper")

_model_cache: Dict[str, WhisperModel] = {}


def _resolve_device(device: str) -> str:
    if device != "auto":
        return device
    return "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"


class WhisperAligner:
    """Транскрибирует аудио через faster-whisper и возвращает word-timestamps.

    Модель кэшируется в памяти процесса — повторные вызовы не перегружают.
    """

    def __init__(
        self,
        model_size: Optional[str] = None,
        language: Optional[str] = None,
        device: Optional[str] = None,
        compute_type: Optional[str] = None,
    ):
        s = get_settings()
        self.model_size = model_size or s.whisper_model
        self.language = language or s.whisper_language
        self.device = _resolve_device(device or s.whisper_device)
        self.compute_type = compute_type or s.whisper_compute_type
        self._model: Optional[WhisperModel] = None

    def _ensure_model(self) -> WhisperModel:
        key = f"{self.model_size}|{self.device}|{self.compute_type}"
        if key in _model_cache:
            self._model = _model_cache[key]
            return self._model
        log.info(
            f"Загружаю whisper: model={self.model_size} device={self.device} "
            f"compute={self.compute_type} (первая загрузка качает модель из HF)"
        )
        model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type,
        )
        _model_cache[key] = model
        self._model = model
        return model

    def transcribe(self, audio_path: Path) -> Dict:
        """Прогнать аудио через whisper и вернуть alignment-структуру.

        Returns:
            {
              "duration": float,
              "language": "ru",
              "words": [{"word": str, "start": float, "end": float, "prob": float}, ...],
              "segments": [{"text": str, "start": float, "end": float}, ...]
            }

        Слова содержат пунктуацию, приклеенную к слову (как whisper отдаёт).
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Аудио не найдено: {audio_path}")

        model = self._ensure_model()
        log.info(f"Транскрибирую {audio_path.name}...")
        segments_iter, info = model.transcribe(
            str(audio_path),
            language=self.language,
            word_timestamps=True,
            vad_filter=False,  # voicer-генерация чистая, VAD не нужен
        )

        words: List[Dict] = []
        segments: List[Dict] = []
        for seg in segments_iter:
            segments.append({
                "text": seg.text.strip(),
                "start": round(seg.start, 3),
                "end": round(seg.end, 3),
            })
            if seg.words:
                for w in seg.words:
                    words.append({
                        "word": w.word.strip(),
                        "start": round(w.start, 3),
                        "end": round(w.end, 3),
                        "prob": round(w.probability, 3),
                    })

        result = {
            "duration": round(info.duration, 3),
            "language": info.language,
            "words": words,
            "segments": segments,
        }
        log.info(
            f"Whisper: {len(words)} слов, {len(segments)} сегментов, "
            f"длительность {info.duration:.1f}s, lang={info.language}"
        )
        return result
