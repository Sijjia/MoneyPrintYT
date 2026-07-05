"""
services/stocks/pexels_videos.py
Pexels Videos API — атмосферные видео-стоки для V1 вместо статичной картинки.

Тот же API key что и у services/images/pexels.py (PEXELS_API_KEY).
Endpoint: https://api.pexels.com/videos/search
Лимит: 200 req/hour, 20000/month — общий с фото.
"""
from pathlib import Path
from typing import Dict, List, Optional

import httpx

from core.config import get_settings
from core.exceptions import APIError, ConfigError
from core.logger import setup_logger

log = setup_logger("pexels-videos")

API_URL = "https://api.pexels.com/videos/search"


class PexelsVideosClient:
    """Pexels Videos для атмосферных B-roll клипов."""

    def __init__(self):
        settings = get_settings()
        if not settings.pexels_api_key:
            raise ConfigError("PEXELS_API_KEY не задан в .env (тот же ключ что и для фото)")
        self.api_key = settings.pexels_api_key
        self.client = httpx.Client(timeout=60.0, headers={"Authorization": self.api_key})

    def search(
        self,
        query: str,
        per_page: int = 5,
        orientation: str = "landscape",
        size: str = "large",
        min_duration: int = 4,
        max_duration: int = 20,
    ) -> List[Dict]:
        """Поиск видео.

        orientation: landscape|portrait|square
        size: large(>=4K)|medium(>=Full HD)|small(>=HD)
        min/max_duration: фильтр по длительности в секундах
        """
        params = {
            "query": query,
            "per_page": per_page,
            "orientation": orientation,
            "size": size,
            "min_duration": min_duration,
            "max_duration": max_duration,
        }
        try:
            r = self.client.get(API_URL, params=params)
            r.raise_for_status()
        except httpx.HTTPError as e:
            raise APIError("PexelsVideos", f"search failed: {e}")
        videos = r.json().get("videos", [])
        log.debug(f"Pexels-videos '{query}' → {len(videos)} clips")
        return videos

    @staticmethod
    def pick_best_file(video: Dict, target_w: int = 1920, target_h: int = 1080) -> Optional[Dict]:
        """Выбирает лучший mp4-файл из вариантов клипа.

        Pexels отдаёт варианты разных разрешений (uhd/hd/sd) + иногда hls. Берём
        mp4-файл ближайший к 1920x1080. HLS отсекается фильтром file_type.
        Если HD есть рядом с 4K — sort выберет HD как ближайший к target.
        """
        files = video.get("video_files") or []
        candidates = [
            f for f in files
            if f.get("file_type", "").lower().startswith("video/mp4")
            and f.get("link")
            and f.get("width") and f.get("height")
        ]
        if not candidates:
            return None
        # Ближе к target по сумме отклонений ширины+высоты; при равенстве — больше площадь
        candidates.sort(key=lambda f: (
            abs(f.get("width", 0) - target_w) + abs(f.get("height", 0) - target_h),
            -(f.get("width", 0) * f.get("height", 0)),
        ))
        return candidates[0]

    def download(self, video: Dict, out_path: Path) -> Path:
        """Скачивает выбранный mp4-вариант видео в файл (stream)."""
        best = self.pick_best_file(video)
        if not best:
            raise APIError("PexelsVideos", f"no usable mp4 in video {video.get('id')}")
        url = best["link"]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self.client.stream("GET", url) as r:
                r.raise_for_status()
                with open(out_path, "wb") as f:
                    for chunk in r.iter_bytes(64 * 1024):
                        f.write(chunk)
        except httpx.HTTPError as e:
            raise APIError("PexelsVideos", f"download failed: {e}")
        return out_path

    def search_and_download(
        self,
        query: str,
        out_path: Path,
        index: int = 0,
        min_duration: int = 4,
        max_duration: int = 20,
    ) -> Optional[Path]:
        """Найти и скачать N-ное подходящее видео. None если не нашлось."""
        videos = self.search(
            query,
            per_page=max(3, index + 1),
            min_duration=min_duration,
            max_duration=max_duration,
        )
        if not videos:
            log.warning(f"Pexels-videos: ничего не найдено по '{query}'")
            return None
        idx = min(index, len(videos) - 1)
        chosen = videos[idx]
        log.debug(
            f"Pexels-videos выбрал id={chosen.get('id')} "
            f"{chosen.get('width')}x{chosen.get('height')} {chosen.get('duration')}s"
        )
        return self.download(chosen, out_path)
