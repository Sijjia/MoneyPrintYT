"""
services/stocks/wikipedia_photo.py
Получение thumbnail-фото исторической личности через Wikipedia REST API.

Без auth. Использует endpoint:
    GET https://ru.wikipedia.org/api/rest_v1/page/summary/{title}

Возвращает thumbnail URL (если есть) + summary. Кэшируем в SQLite + downloaded
файлы в указанную папку.
"""
from pathlib import Path
from typing import Optional

import httpx

from core.exceptions import APIError
from core.logger import setup_logger

log = setup_logger("wiki_photo")

API_RU = "https://ru.wikipedia.org/api/rest_v1/page/summary/"
API_EN = "https://en.wikipedia.org/api/rest_v1/page/summary/"
USER_AGENT = "webik-pipeline/0.1 (https://youtube.com/@WebikStudio)"


class WikipediaPhotoClient:
    def __init__(self):
        self.client = httpx.Client(
            timeout=15.0,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        )

    def fetch_summary(self, title: str, lang: str = "ru") -> Optional[dict]:
        """GET /page/summary/{title}. Возвращает dict или None если не найдено."""
        base = API_RU if lang == "ru" else API_EN
        url = base + httpx.URL(title.replace(" ", "_")).path
        try:
            r = self.client.get(url)
            if r.status_code == 404:
                return None
            r.raise_for_status()
        except httpx.HTTPError as e:
            log.warning(f"Wikipedia summary failed для '{title}' ({lang}): {e}")
            return None
        return r.json()

    def get_thumbnail_url(self, title: str) -> Optional[str]:
        """Сначала ищем в ru-wiki, fallback en-wiki. Возвращаем оригинальный URL."""
        for lang in ("ru", "en"):
            data = self.fetch_summary(title, lang=lang)
            if not data:
                continue
            # originalimage предпочтительнее thumbnail (больший размер)
            for key in ("originalimage", "thumbnail"):
                img = data.get(key)
                if img and img.get("source"):
                    return img["source"]
        return None

    def download_photo(self, title: str, out_path: Path) -> Optional[Path]:
        """Скачивает фото по имени personality. None если не найдено."""
        url = self.get_thumbnail_url(title)
        if not url:
            return None
        out_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            r = self.client.get(url)
            r.raise_for_status()
        except httpx.HTTPError as e:
            log.warning(f"Wikipedia photo download failed для '{title}': {e}")
            return None
        out_path.write_bytes(r.content)
        return out_path
