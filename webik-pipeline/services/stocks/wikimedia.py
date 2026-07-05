"""
services/stocks/wikimedia.py
Поиск + скачивание реальных архивных фото из Wikimedia Commons.

Без API-ключа, через MediaWiki action API. Подходит для:
- Исторические события (фото СССР, ВОВ, Холодной войны)
- Реальные люди (политики, деятели, преступники)
- Документальная съёмка событий

Все файлы в Commons лицензированы CC-BY/CC-BY-SA/PD — можно использовать
с указанием атрибуции (для YouTube → в описание видео).

API: https://commons.wikimedia.org/w/api.php
"""
from pathlib import Path
from typing import Dict, List, Optional

import httpx

from core.exceptions import APIError
from core.logger import setup_logger

log = setup_logger("wikimedia")

API_URL = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "webik-pipeline/0.1 (https://youtube.com/@WebikStudio)"


class WikimediaClient:
    """Клиент Wikimedia Commons. Без auth, всё public."""

    def __init__(self):
        self.client = httpx.Client(
            timeout=30.0,
            headers={"User-Agent": USER_AGENT},
        )

    def search_images(
        self,
        query: str,
        limit: int = 10,
        min_width: int = 1280,
    ) -> List[Dict]:
        """Возвращает список dict с url+title+width/height отфильтрованных по min_width.

        Использует generator=search для поиска в namespace 6 (File:),
        + imageinfo для получения URL.
        """
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": f"filetype:bitmap {query}",
            "gsrnamespace": 6,  # File: namespace
            "gsrlimit": limit,
            "prop": "imageinfo",
            "iiprop": "url|size|mime",
            "iiurlwidth": 1920,  # запросить thumb до 1920px
        }
        try:
            r = self.client.get(API_URL, params=params)
            r.raise_for_status()
        except httpx.HTTPError as e:
            raise APIError("Wikimedia", f"search failed: {e}")
        pages = r.json().get("query", {}).get("pages", {}) or {}
        results: List[Dict] = []
        for page in pages.values():
            ii = (page.get("imageinfo") or [{}])[0]
            url = ii.get("thumburl") or ii.get("url")
            if not url:
                continue
            width = ii.get("thumbwidth") or ii.get("width") or 0
            height = ii.get("thumbheight") or ii.get("height") or 0
            mime = ii.get("mime", "")
            if width < min_width:
                continue
            if not mime.startswith("image/"):
                continue
            results.append({
                "title": page.get("title"),
                "url": url,
                "width": width,
                "height": height,
                "mime": mime,
            })
        log.debug(f"Wikimedia '{query}' → {len(results)} hits (>= {min_width}px)")
        return results

    def download(self, hit: Dict, out_path: Path) -> Path:
        url = hit.get("url")
        if not url:
            raise APIError("Wikimedia", "no url in hit")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            r = self.client.get(url)
            r.raise_for_status()
        except httpx.HTTPError as e:
            raise APIError("Wikimedia", f"download failed: {e}")
        out_path.write_bytes(r.content)
        return out_path

    def search_and_download(
        self,
        query: str,
        out_path: Path,
        index: int = 0,
        min_width: int = 1280,
    ) -> Optional[Path]:
        hits = self.search_images(query, limit=max(3, index + 1), min_width=min_width)
        if not hits:
            log.warning(f"Wikimedia: ничего не найдено по '{query}'")
            return None
        idx = min(index, len(hits) - 1)
        return self.download(hits[idx], out_path)
