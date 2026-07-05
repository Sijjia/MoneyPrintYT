"""
services/tts/elevenlabs.py
Обёртка над ElevenLabs Multilingual v2 для генерации голоса диктора.

Использование:
    tts = ElevenLabsTTS()
    tts.synthesize("Привет, мир", out_path=Path("voice.mp3"))
"""
from pathlib import Path
from typing import Optional

from elevenlabs import ElevenLabs, VoiceSettings

from core.config import get_settings
from core.exceptions import APIError, ConfigError
from core.logger import setup_logger

log = setup_logger("elevenlabs")

DEFAULT_MODEL = "eleven_multilingual_v2"
DEFAULT_OUTPUT_FORMAT = "mp3_44100_128"


class ElevenLabsTTS:
    """Высокоуровневая обёртка для генерации голоса.

    Поддерживает маркер `[пауза N.Nс]` в тексте — заменяется на SSML-тег break,
    либо разбивается на сегменты с явной паузой если voice не поддерживает SSML.
    """

    def __init__(
        self,
        voice_id: Optional[str] = None,
        model: str = DEFAULT_MODEL,
    ):
        settings = get_settings()
        if not settings.elevenlabs_api_key:
            raise ConfigError("ELEVENLABS_API_KEY не задан в .env")
        self.voice_id = voice_id or settings.elevenlabs_voice_id
        if not self.voice_id:
            raise ConfigError("ELEVENLABS_VOICE_ID не задан в .env")
        self.client = ElevenLabs(api_key=settings.elevenlabs_api_key)
        self.model = model

    def synthesize(
        self,
        text: str,
        out_path: Path,
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        style: float = 0.0,
        speed: float = 1.0,
    ) -> Path:
        """Сгенерировать mp3 из текста. Возвращает путь к файлу."""
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # ElevenLabs понимает <break time="1.5s"/> в тексте напрямую.
        # Конвертируем наш формат [пауза 1.5с] → SSML break.
        prepared_text = self._convert_pause_markers(text)

        try:
            audio_stream = self.client.text_to_speech.convert(
                voice_id=self.voice_id,
                model_id=self.model,
                text=prepared_text,
                output_format=DEFAULT_OUTPUT_FORMAT,
                voice_settings=VoiceSettings(
                    stability=stability,
                    similarity_boost=similarity_boost,
                    style=style,
                    speed=speed,
                ),
            )
        except Exception as e:
            raise APIError("ElevenLabs", f"TTS failed: {e}")

        with open(out_path, "wb") as f:
            for chunk in audio_stream:
                if chunk:
                    f.write(chunk)

        log.info(f"TTS → {out_path} ({out_path.stat().st_size // 1024} KB)")
        return out_path

    @staticmethod
    def _convert_pause_markers(text: str) -> str:
        import re

        def replace(match):
            seconds = match.group(1).replace(",", ".")
            return f'<break time="{seconds}s"/>'

        return re.sub(r"\[пауза\s+([0-9.,]+)\s*с\]", replace, text)
