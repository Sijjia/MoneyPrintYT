"""
core/config.py
Загрузка конфигурации из .env через pydantic-settings.
Использует validation чтобы упасть рано если ключ забыли.
"""
from pathlib import Path
from typing import Optional, Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Все настройки пайплайна. Подгружаются из .env автоматически."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # === LLM ===
    anthropic_api_key: str = Field(..., description="Anthropic Claude API key")

    # === TTS (Voicer API — обёртка над ElevenLabs через voiceapi.csv666.ru) ===
    voicer_api_key: Optional[str] = None
    voicer_template_uuid: Optional[str] = None  # UUID шаблона голоса (например, "Webik V3")
    voicer_base_url: str = "https://voiceapi.csv666.ru"
    # Длинный текст ElevenLabs дрейфит и режется Voicer'ом вслепую (швы посреди фраз).
    # Бьём сами по границам предложений на куски ≤ этого лимита, швы прячем в паузы.
    voicer_max_chunk_chars: int = 2500

    # === fal.ai ===
    fal_key: Optional[str] = None

    # === Stocks ===
    pexels_api_key: Optional[str] = None
    unsplash_access_key: Optional[str] = None
    pixabay_api_key: Optional[str] = None

    # === Other services ===
    immersity_api_key: Optional[str] = None
    suno_api_key: Optional[str] = None
    freesound_api_key: Optional[str] = None

    # === YouTube ===
    youtube_client_secrets_path: Path = Path("./youtube_credentials.json")
    youtube_token_path: Path = Path("./youtube_token.json")
    # yt-dlp cookies для скачивания вырезок (visual.type=youtube_clip).
    # Один из двух (file приоритетнее browser):
    yt_cookies_file: Optional[Path] = None
    yt_cookies_browser: Optional[str] = None  # "chrome"|"firefox"|"edge"

    # === Telegram ===
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None

    # === Premiere ===
    premiere_path: Optional[str] = None

    # === Channel branding ===
    channel_name: str = "WEBIK STUDIO"
    channel_handle: str = "@WebikStudio"

    # === Mascot ===
    mascot_bebrik_path: Optional[Path] = Path(r"E:\OBS STREAM\бебрик.mov")

    # === Pack media (overlay assets) ===
    pack_media_root: Optional[Path] = Path(r"E:\YouTube Webik\Pack media")
    film_burn_dir: Optional[Path] = Path(r"E:\YouTube Webik\Pack media\FILM BURN (WITH SFX)")
    ncs_music_dir: Optional[Path] = Path(r"E:\YouTube Webik\Pack media\NCS MUSIC (I USE)")
    sfx_dir: Optional[Path] = Path(r"E:\YouTube Webik\Sound\Old Sport SFX Pack")

    # === Pipeline ===
    default_video_resolution: str = "1920x1080"
    default_framerate: int = 30
    assets_quality: Literal["low", "medium", "high"] = "high"
    use_local_depth: bool = False
    use_local_whisper: bool = True

    # === faster-whisper ===
    whisper_model: str = "medium"  # tiny|base|small|medium|large-v3
    whisper_device: Literal["cpu", "cuda", "auto"] = "auto"
    whisper_compute_type: str = "int8"  # int8|int8_float16|float16|float32
    whisper_language: str = "ru"

    # === Paths ===
    projects_dir: Path = Path("./projects")
    templates_dir: Path = Path("./templates")
    luts_dir: Path = Path("./luts")
    overlays_dir: Path = Path("./overlays")
    presets_dir: Path = Path("./presets")
    prompts_dir: Path = Path("./services/llm/prompts")

    @property
    def video_width(self) -> int:
        return int(self.default_video_resolution.split("x")[0])

    @property
    def video_height(self) -> int:
        return int(self.default_video_resolution.split("x")[1])


# Singleton
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Lazy singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
