"""
services/stocks/pixabay.py
Свой клиент Pixabay API (фото + видео).

Pixabay GitHub-обёртки заброшены, поэтому пишем сами — ~30 строк на endpoint.
- Photos: https://pixabay.com/api/?key=KEY&q=QUERY
- Videos: https://pixabay.com/api/videos/?key=KEY&q=QUERY

Бесплатно: 100 req / 60 sec, ~20000/месяц.
"""
from pathlib import Path
from typing import Dict, List, Optional

import httpx

from core.config import get_settings
from core.exceptions import APIError, ConfigError
from core.logger import setup_logger

log = setup_logger("pixabay")

PHOTOS_URL = "https://pixabay.com/api/"
VIDEOS_URL = "https://pixabay.com/api/videos/"


class PixabayClient:
    """Клиент Pixabay для поиска и скачивания фото/видео."""

    def __init__(self):
        settings = get_settings()
        if not settings.pixabay_api_key:
            raise ConfigError(
                "PIXABAY_API_KEY не задан в .env "
                "(зарегистрируйся на pixabay.com → доку API → ключ в URL примера)"
            )
        self.api_key = settings.pixabay_api_key
        self.client = httpx.Client(timeout=30.0)

    def search_photos(
        self,
        query: str,
        per_page: int = 5,
        orientation: str = "horizontal",
        min_width: int = 1920,
    ) -> List[Dict]:
        """Поиск фото. orientation: all|horizontal|vertical."""
        params = {
            "key": self.api_key,
            "q": query,
            "per_page": max(3, per_page),  # Pixabay min = 3
            "orientation": orientation,
            "min_width": min_width,
            "image_type": "photo",
            "safesearch": "true",
        }
        try:
            r = self.client.get(PHOTOS_URL, params=params)
            r.raise_for_status()
        except httpx.HTTPError as e:
            raise APIError("Pixabay", f"photos search failed: {e}")
        hits = r.json().get("hits", [])
        log.debug(f"Pixabay photos '{query}' → {len(hits)} hits")
        return hits

    def search_videos(
        self,
        query: str,
        per_page: int = 5,
        video_type: str = "all",
        min_width: int = 1920,
    ) -> List[Dict]:
        """Поиск видео. video_type: all|film|animation."""
        params = {
            "key": self.api_key,
            "q": query,
            "per_page": max(3, per_page),
            "video_type": video_type,
            "min_width": min_width,
            "safesearch": "true",
        }
        try:
            r = self.client.get(VIDEOS_URL, params=params)
            r.raise_for_status()
        except httpx.HTTPError as e:
            raise APIError("Pixabay", f"videos search failed: {e}")
        hits = r.json().get("hits", [])
        log.debug(f"Pixabay videos '{query}' → {len(hits)} hits")
        return hits

    def download_photo(
        self,
        hit: Dict,
        out_path: Path,
        size_key: str = "largeImageURL",
    ) -> Path:
        """Скачивает фото. size_key: previewURL|webformatURL|largeImageURL|fullHDURL|imageURL."""
        url = hit.get(size_key) or hit.get("largeImageURL") or hit.get("webformatURL")
        if not url:
            raise APIError("Pixabay", f"no usable photo URL in hit: {hit.keys()}")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            r = self.client.get(url)
            r.raise_for_status()
        except httpx.HTTPError as e:
            raise APIError("Pixabay", f"photo download failed: {e}")
        out_path.write_bytes(r.content)
        return out_path

    def download_video(
        self,
        hit: Dict,
        out_path: Path,
        quality: str = "large",
    ) -> Path:
        """Скачивает видео. quality: large|medium|small|tiny."""
        videos = hit.get("videos") or {}
        chosen = videos.get(quality) or videos.get("medium") or videos.get("small")
        if not chosen or not chosen.get("url"):
            raise APIError("Pixabay", f"no usable video URL in hit (qualities: {list(videos.keys())})")
        url = chosen["url"]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self.client.stream("GET", url) as r:
                r.raise_for_status()
                with open(out_path, "wb") as f:
                    for chunk in r.iter_bytes(64 * 1024):
                        f.write(chunk)
        except httpx.HTTPError as e:
            raise APIError("Pixabay", f"video download failed: {e}")
        return out_path

    def search_and_download_photo(
        self,
        query: str,
        out_path: Path,
        index: int = 0,
    ) -> Optional[Path]:
        """Найти и скачать N-ную подходящую фотку. None если ничего не найдено."""
        hits = self.search_photos(query, per_page=max(3, index + 1))
        if not hits:
            log.warning(f"Pixabay photos: ничего не найдено по '{query}'")
            return None
        idx = min(index, len(hits) - 1)
        return self.download_photo(hits[idx], out_path)

    def search_and_download_video(
        self,
        query: str,
        out_path: Path,
        index: int = 0,
        quality: str = "large",
    ) -> Optional[Path]:
        """Найти и скачать N-ное видео. None если ничего не найдено."""
        hits = self.search_videos(query, per_page=max(3, index + 1))
        if not hits:
            log.warning(f"Pixabay videos: ничего не найдено по '{query}'")
            return None
        idx = min(index, len(hits) - 1)
        return self.download_video(hits[idx], out_path, quality=quality)
