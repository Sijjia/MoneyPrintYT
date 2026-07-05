"""
services/images/pexels.py
Поиск + скачивание стоковых фото с Pexels.

Бесплатный API, лимит 200 запросов/час, 20000/месяц.
"""
from pathlib import Path
from typing import List, Optional, Dict

import httpx

from core.config import get_settings
from core.exceptions import APIError, ConfigError
from core.logger import setup_logger

log = setup_logger("pexels")

API_URL = "https://api.pexels.com/v1/search"


class PexelsClient:
    def __init__(self):
        settings = get_settings()
        if not settings.pexels_api_key:
            raise ConfigError("PEXELS_API_KEY не задан в .env (получи на pexels.com/api)")
        self.api_key = settings.pexels_api_key
        self.client = httpx.Client(timeout=30.0, headers={"Authorization": self.api_key})

    def search(
        self,
        query: str,
        per_page: int = 5,
        orientation: str = "landscape",
        size: str = "large",
    ) -> List[Dict]:
        """Поиск фотографий. Возвращает список dict с метаданными."""
        params = {
            "query": query,
            "per_page": per_page,
            "orientation": orientation,
            "size": size,
        }
        try:
            r = self.client.get(API_URL, params=params)
            r.raise_for_status()
        except httpx.HTTPError as e:
            raise APIError("Pexels", f"search failed: {e}")
        photos = r.json().get("photos", [])
        log.debug(f"Pexels '{query}' → {len(photos)} photos")
        return photos

    def download(self, photo: Dict, out_path: Path, size_key: str = "large2x") -> Path:
        """Скачивает фото в файл. size_key: original, large2x, large, medium."""
        url = photo["src"].get(size_key) or photo["src"]["large"]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            r = self.client.get(url)
            r.raise_for_status()
        except httpx.HTTPError as e:
            raise APIError("Pexels", f"download failed: {e}")
        out_path.write_bytes(r.content)
        return out_path

    def search_and_download(
        self,
        query: str,
        out_path: Path,
        index: int = 0,
    ) -> Optional[Path]:
        """Найти и скачать первую (или N-ную) подходящую фотку. None если не нашлось."""
        photos = self.search(query, per_page=max(1, index + 1))
        if not photos:
            log.warning(f"Pexels: ничего не найдено по '{query}'")
            return None
        idx = min(index, len(photos) - 1)
        return self.download(photos[idx], out_path)
