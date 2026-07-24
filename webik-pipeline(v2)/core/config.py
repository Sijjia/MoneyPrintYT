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
    anthropic_api_key: str = Field("", description="Anthropic Claude API key")
    # OpenRouter — альтернатива прямому Anthropic API (один ключ на всех
    # провайдеров, OpenAI-формат). Если задан OPENROUTER_API_KEY в .env, все
    # LLM-вызовы идут через OpenRouter. Модель — через LLM_MODEL (строкой в
    # формате OpenRouter, напр. "anthropic/claude-sonnet-4.5" или
    # "google/gemini-2.5-flash"); по умолчанию Sonnet 4.5.
    openrouter_api_key: Optional[str] = None
    llm_model: Optional[str] = None
    # Дешёвая модель для МЕХАНИЧЕСКИХ стадий (раскадровка Stage 3, выбор клипа
    # Stage 4) — там не нужен топ-креатив, а вызовов много. Экономит ~90% стоимости
    # ролика. Задать: LLM_MODEL_CHEAP=google/gemini-2.5-flash. Пусто → llm_model.
    llm_model_cheap: Optional[str] = None
    # Веб-ресёрч темы перед Stage 1 (OpenRouter :online). Для хайповых/свежих тем
    # подтягивает реальные факты из интернета. Включить: WEB_RESEARCH=true
    web_research: bool = False

    # === Notion ===
    # Internal integration token (notion.so/my-integrations). Нужен доступ к
    # страницам/базе со сценариями (расшарить интеграции). Читаем сценарии-
    # референсы для style-guide + при желании сохраняем готовые.
    notion_token: Optional[str] = None
    notion_scripts_db_id: Optional[str] = None  # опц.: id базы со сценариями
    # Родительская страница, под которую сохранять готовые сценарии. По умолчанию
    # — страница «Webik» (там лежат все 11 его айсбергов). Override через .env.
    notion_scripts_parent_id: Optional[str] = "27eb7fae-11c4-80ca-b658-cbb50f152ff2"
    # Авто-сохранение готового сценария (Stage 2) в Notion. Off по умолчанию,
    # чтобы тестовые прогоны не плодили страницы. Включить: NOTION_SAVE_SCRIPTS=true
    notion_save_scripts: bool = False

    # === TTS (Voicer API — обёртка над ElevenLabs через voiceapi.csv666.ru) ===
    voicer_api_key: Optional[str] = None
    voicer_template_uuid: Optional[str] = None  # UUID шаблона голоса (например, "Webik V3")
    voicer_base_url: str = "https://voiceapi.csv666.ru"
    # Длинный текст ElevenLabs дрейфит и режется Voicer'ом вслепую (швы посреди фраз).
    # Бьём сами по границам предложений на куски ≤ этого лимита, швы прячем в паузы.
    voicer_max_chunk_chars: int = 2500

    # === TTS (Lumean — api.lumean.app, обёртка над ElevenLabs; заказ→поллинг→скачать) ===
    tts_provider: str = "voicer"  # "voicer" | "lumean"
    lumean_api_key: Optional[str] = None
    lumean_base_url: str = "https://api.lumean.app/api/public"
    lumean_template_uuid: Optional[str] = None  # UUID TTS-шаблона (создаём один раз)
    # Модель ElevenLabs через Lumean: eleven_v3 (стабильнее) / eleven_multilingual_v2
    lumean_model_id: str = "eleven_multilingual_v2"
    lumean_voice_id: Optional[str] = None  # voice_id из библиотеки (если создаём шаблон в коде)

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
    # Авто-подбор архивного видео с YouTube для сцен-фактов (NER-сущность или
    # явный visual.type=archive_video). Off по умолчанию — чтобы обычные прогоны
    # не лезли качать ролики. Включается через .env: YOUTUBE_AUTO_ARCHIVE=true
    youtube_auto_archive: bool = False

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
