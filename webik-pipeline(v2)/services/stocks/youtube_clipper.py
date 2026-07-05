"""
services/stocks/youtube_clipper.py
Вырезает фрагмент из YouTube-ролика как локальный mp4 для использования
в качестве «доказательного» B-roll (архивные кадры, реакции, интервью).

Pipeline:
1. yt-dlp скачивает best mp4 (с audio) с YouTube
2. ffmpeg вырезает [clip_start, clip_end], стрипит audio (на V1 не нужен)
3. Возвращает локальный mp4 готовый к импорту в Premiere

Юр. серая зона: используй только public-видео где fair-use очевиден
(news clips, public events, archive). Caption (атрибуция автора) сохраняется
в manifest для будущей вставки в end-screen.

Свой код вместо github.com/bradautomates/claude-video — yt-dlp + ffmpeg
известны и стабильны, не нужна сторонняя обёртка.
"""
import os
import shutil
from pathlib import Path
from typing import Dict, Optional

from core.exceptions import APIError
from core.logger import setup_logger

log = setup_logger("youtube-clipper")

# Кэш-директория где хранятся скачанные оригиналы (чтобы не качать заново
# при повторном clip из того же видео)
DOWNLOAD_CACHE_SUBDIR = "_yt_cache"


def _video_id_from_url(url: str) -> str:
    """Извлекает video id из YouTube URL для cache filename."""
    import hashlib
    return hashlib.md5(url.encode("utf-8")).hexdigest()[:12]


def download_full_video(url: str, cache_dir: Path) -> Optional[Path]:
    """Скачивает best mp4 с YouTube в cache_dir. Кеш по url-hash.

    Если YouTube блокирует anonymous (typical с 2024+), нужны cookies.
    Поддерживаемые механизмы:
    - env `YT_COOKIES_BROWSER=firefox|chrome|edge` → берёт cookies из браузера
    - env `YT_COOKIES_FILE=/path/to/cookies.txt` → файл cookies в Netscape-формате
    Без cookies работает только на видео без «sign in to confirm» гейта.

    Returns Path к скачанному mp4 или None при ошибке.
    """
    try:
        import yt_dlp  # noqa: F401
    except ImportError:
        log.warning("yt-dlp не установлен (pip install yt-dlp)")
        return None

    cache_dir.mkdir(parents=True, exist_ok=True)
    vid_id = _video_id_from_url(url)
    out_path = cache_dir / f"{vid_id}.mp4"
    if out_path.exists() and out_path.stat().st_size > 10_000:
        log.info(f"  yt-dlp cache hit: {out_path.name}")
        return out_path

    try:
        from yt_dlp import YoutubeDL
        ydl_opts = {
            # Relaxed: bestvideo+bestaudio с любым codec, потом best как fallback.
            # YouTube постоянно меняет form'ы — слишком строгий селектор валится.
            "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
            "merge_output_format": "mp4",
            "outtmpl": str(cache_dir / f"{vid_id}.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
        }
        # Cookies для обхода bot-detection (YouTube часто требует с 2024+).
        # Источники в порядке приоритета: env (ad-hoc override) → .env через Settings.
        _apply_cookies(ydl_opts)
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        msg = str(e)
        if "Sign in to confirm" in msg or "bot" in msg.lower():
            log.warning(
                f"  YouTube требует cookies. Установи env YT_COOKIES_BROWSER=chrome "
                f"(или firefox/edge — браузер где ты залогинен). URL: {url}"
            )
        else:
            log.warning(f"  yt-dlp download failed для {url}: {msg[:200]}")
        return None

    # yt-dlp может назвать файл как .mp4 или .mkv (если merge упал) — ищем по prefix
    candidates = sorted(cache_dir.glob(f"{vid_id}.*"))
    mp4s = [p for p in candidates if p.suffix.lower() == ".mp4" and p.stat().st_size > 10_000]
    if mp4s:
        return mp4s[0]
    log.warning(f"  yt-dlp не оставил mp4 для {url}")
    return None


def _apply_cookies(ydl_opts: dict) -> None:
    """Прокидывает cookies (env → Settings) в ydl_opts — общий код для
    полного и секционного скачивания."""
    cookies_browser = os.environ.get("YT_COOKIES_BROWSER")
    cookies_file = os.environ.get("YT_COOKIES_FILE")
    if not cookies_browser and not cookies_file:
        try:
            from core.config import get_settings
            s = get_settings()
            if s.yt_cookies_file:
                cookies_file = str(s.yt_cookies_file)
            elif s.yt_cookies_browser:
                cookies_browser = s.yt_cookies_browser
        except Exception:
            pass
    if cookies_file and Path(cookies_file).exists():
        ydl_opts["cookiefile"] = cookies_file
    elif cookies_browser:
        ydl_opts["cookiesfrombrowser"] = (cookies_browser,)


def download_section(
    url: str, cache_dir: Path, clip_start: float, clip_end: float
) -> Optional[Path]:
    """Скачивает ТОЛЬКО окно [clip_start, clip_end] через yt-dlp download_ranges
    (force_keyframes_at_cuts). Для длинных архивных роликов (хроника на 30-50 мин)
    это качает мегабайты вместо гигабайтов. Файл начинается ~с clip_start.

    Возвращает Path к секции (~окно, с аудио) или None — тогда fetch_clip
    откатывается на полное скачивание.
    """
    try:
        from yt_dlp import YoutubeDL
        from yt_dlp.utils import download_range_func
    except ImportError:
        return None

    cache_dir.mkdir(parents=True, exist_ok=True)
    vid_id = _video_id_from_url(url)
    tag = f"{vid_id}_{int(clip_start)}_{int(clip_end)}"
    out_path = cache_dir / f"{tag}.mp4"
    if out_path.exists() and out_path.stat().st_size > 10_000:
        log.info(f"  yt-dlp section cache hit: {out_path.name}")
        return out_path

    try:
        ydl_opts = {
            "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
            "merge_output_format": "mp4",
            "outtmpl": str(cache_dir / f"{tag}.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "download_ranges": download_range_func(None, [(clip_start, clip_end)]),
            "force_keyframes_at_cuts": True,
        }
        _apply_cookies(ydl_opts)
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        log.info(f"  секционное скачивание не вышло ({str(e)[:120]}) — полное")
        return None

    cands = [p for p in sorted(cache_dir.glob(f"{tag}.*"))
             if p.suffix.lower() == ".mp4" and p.stat().st_size > 10_000]
    return cands[0] if cands else None


def trim_clip(
    source_mp4: Path,
    clip_start: float,
    clip_end: float,
    out_path: Path,
    strip_audio: bool = True,
) -> Optional[Path]:
    """ffmpeg trim [clip_start, clip_end]. На V1 кладём silent (audio на A1)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists() and out_path.stat().st_size > 1000:
        return out_path

    try:
        import ffmpeg
        stream = ffmpeg.input(str(source_mp4), ss=clip_start, to=clip_end)
        kwargs = {}
        if strip_audio:
            kwargs["an"] = None
        # Re-encode (не stream copy) чтобы тайминг был точный по seconds
        # — copy не работает по non-keyframe boundaries
        (
            stream.output(
                str(out_path),
                vcodec="libx264", crf=20, preset="fast", pix_fmt="yuv420p",
                **kwargs,
            )
            .overwrite_output()
            .global_args("-loglevel", "error")
            .run(quiet=True)
        )
        return out_path
    except Exception as e:
        log.warning(f"  ffmpeg trim failed: {e}")
        return None


def fetch_clip(
    url: str,
    clip_start: float,
    clip_end: float,
    project_dir: Path,
    scene_id: str,
    caption: str = "",
) -> Optional[Dict]:
    """Скачивает + вырезает YouTube-клип. Возвращает dict с метаданными
    или None при ошибке.

    Output: project_dir / assets / youtube_clips / {scene_id}.mp4
    """
    if clip_end <= clip_start:
        log.warning(f"  {scene_id}: clip_end ({clip_end}) <= clip_start ({clip_start})")
        return None

    cache_dir = project_dir / "assets" / DOWNLOAD_CACHE_SUBDIR
    out_dir = project_dir / "assets" / "youtube_clips"
    out_path = out_dir / f"{scene_id}.mp4"

    # Сначала пробуем скачать ТОЛЬКО окно (быстро для длинных архивов). Секция
    # начинается ~с clip_start → режем относительно (0 → длительность окна).
    # Если секция не вышла — откат на полное скачивание + абсолютный трим.
    section = download_section(url, cache_dir, clip_start, clip_end)
    if section is not None:
        trimmed = trim_clip(section, 0.0, clip_end - clip_start, out_path)
    else:
        full = download_full_video(url, cache_dir)
        if full is None:
            return None
        trimmed = trim_clip(full, clip_start, clip_end, out_path)
    if trimmed is None:
        return None

    log.info(
        f"  yt clip {scene_id}: {url} [{clip_start:.1f}s-{clip_end:.1f}s] "
        f"→ {trimmed.name} ({trimmed.stat().st_size // 1024} KB)"
    )
    return {
        "path": trimmed,
        "duration_sec": clip_end - clip_start,
        "source_url": url,
        "caption": caption,
    }
