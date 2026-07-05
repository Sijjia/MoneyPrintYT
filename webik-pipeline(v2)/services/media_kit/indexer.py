"""
services/media_kit/indexer.py
CLIP-индексатор старой медиатеки Webik (E:\\YouTube Webik\\{N}\\медиа\\).

Что делает:
- Сканирует roots для .jpg/.png/.webp/.mp4/.mov/.mkv
- Для каждой картинки → CLIP image embedding (ViT-B-32, openai weights)
- Для каждого видео → middle frame через ffmpeg → CLIP image embedding
- Хранит в SQLite (метаданные) + numpy .npy (эмбеддинги)
- Incremental: уже-проиндексированные файлы (по path+size+mtime) пропускает

Размер: 512 float per file (ViT-B-32). 1390 файлов ≈ 2.8 MB embeds + ~100KB SQLite.

Производительность: ~50 файлов/сек на CPU (картинки), ~5 файлов/сек (видео — ffmpeg).
"""
import sqlite3
import time
from io import BytesIO
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import ffmpeg
import numpy as np
import open_clip
import torch
from PIL import Image

from core.logger import setup_logger

log = setup_logger("indexer")

# ViT-B-32 — самая лёгкая CLIP модель, ~150MB веса. Достаточно для семантического поиска
# по короткому query типа "korean shaman ritual".
MODEL_NAME = "ViT-B-32"
MODEL_PRETRAINED = "openai"
EMBED_DIM = 512

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm"}


class MediaIndexer:
    """Сканер + кодировщик CLIP для медиа-файлов.

    Использование:
        idx = MediaIndexer(index_dir=Path(".media_index"))
        idx.load_model()  # отложенная загрузка (~5 сек)
        idx.index_root(Path(r"E:\\YouTube Webik"))
        idx.flush()  # сохранить embeds.npy
    """

    def __init__(self, index_dir: Path):
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.index_dir / "db.sqlite"
        self.embeds_path = self.index_dir / "embeds.npy"
        self.db = self._connect_db()
        self._load_existing_embeds()
        self.model = None
        self.preprocess = None

    def _connect_db(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS media (
                path TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                embed_idx INTEGER NOT NULL,
                file_size INTEGER NOT NULL,
                file_mtime REAL NOT NULL,
                indexed_at REAL NOT NULL
            )
        """)
        conn.commit()
        return conn

    def _load_existing_embeds(self) -> None:
        """Загружаем существующие эмбеддинги в self.embeds (N × 512)."""
        if self.embeds_path.exists():
            self.embeds = np.load(self.embeds_path)
            log.info(f"Загружено {len(self.embeds)} существующих эмбеддингов")
        else:
            self.embeds = np.zeros((0, EMBED_DIM), dtype=np.float32)

    def load_model(self):
        """Ленивая загрузка CLIP модели (один раз)."""
        if self.model is not None:
            return
        log.info(f"Загружаю CLIP {MODEL_NAME} ({MODEL_PRETRAINED})...")
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            MODEL_NAME, pretrained=MODEL_PRETRAINED
        )
        self.model.eval()
        log.info("CLIP готов")

    def index_root(
        self,
        root: Path,
        subdir_filter: Optional[str] = "медиа",
    ) -> Tuple[int, int]:
        """Индексирует медиа-файлы под root.

        Args:
            root: корневая папка (например E:\\YouTube Webik\\)
            subdir_filter: если задан — индексируем только файлы внутри подпапок
                с таким именем (например "медиа"). None → все файлы под root.

        Returns:
            (новых файлов, пропущено уже-индексированных)
        """
        self.load_model()
        files = list(self._discover(root, subdir_filter))
        log.info(f"Найдено {len(files)} файлов под {root}")
        new_count, skip_count = 0, 0
        t0 = time.time()
        for i, path in enumerate(files):
            if (i + 1) % 50 == 0:
                elapsed = time.time() - t0
                rate = (i + 1) / max(0.01, elapsed)
                eta = (len(files) - i - 1) / max(0.01, rate)
                log.info(f"  {i+1}/{len(files)} ({rate:.1f} файл/сек, eta {eta:.0f}с)")
            if self._is_indexed_and_fresh(path):
                skip_count += 1
                continue
            try:
                embed = self._encode_file(path)
                self._save(path, embed)
                new_count += 1
            except Exception as e:
                log.warning(f"  не смог обработать {path.name}: {e}")
        self.flush()
        log.info(
            f"Индексирование завершено: +{new_count} новых, {skip_count} пропущено "
            f"(уже актуальны), всего в индексе {len(self.embeds)}"
        )
        return new_count, skip_count

    def _discover(self, root: Path, subdir_filter: Optional[str]) -> Iterable[Path]:
        """Рекурсивно ищет медиа-файлы. Если subdir_filter задан — только в папках с таким именем."""
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            ext = p.suffix.lower()
            if ext not in IMAGE_EXTS and ext not in VIDEO_EXTS:
                continue
            if subdir_filter and subdir_filter not in [pp.name for pp in p.parents]:
                continue
            yield p

    def _is_indexed_and_fresh(self, path: Path) -> bool:
        """True если файл уже в индексе и его size+mtime не менялись."""
        cur = self.db.execute(
            "SELECT file_size, file_mtime FROM media WHERE path = ?", (str(path),)
        ).fetchone()
        if not cur:
            return False
        try:
            stat = path.stat()
        except OSError:
            return False
        return cur[0] == stat.st_size and abs(cur[1] - stat.st_mtime) < 0.01

    def _encode_file(self, path: Path) -> np.ndarray:
        ext = path.suffix.lower()
        if ext in IMAGE_EXTS:
            return self._encode_image_file(path)
        if ext in VIDEO_EXTS:
            return self._encode_video_file(path)
        raise ValueError(f"unknown ext: {ext}")

    def _encode_image_file(self, path: Path) -> np.ndarray:
        img = Image.open(path).convert("RGB")
        return self._encode_pil(img)

    def _encode_video_file(self, path: Path) -> np.ndarray:
        """Извлекает middle frame через ffmpeg в память и кодирует."""
        try:
            probe = ffmpeg.probe(str(path))
            duration = float(probe["format"]["duration"])
        except Exception:
            duration = 1.0
        mid = max(0.1, duration / 2.0)
        out, _ = (
            ffmpeg.input(str(path), ss=mid)
            .output("pipe:", vframes=1, format="image2", vcodec="mjpeg")
            .run(capture_stdout=True, capture_stderr=True, quiet=True)
        )
        if not out:
            raise RuntimeError("ffmpeg не вернул frame")
        img = Image.open(BytesIO(out)).convert("RGB")
        return self._encode_pil(img)

    def _encode_pil(self, img: Image.Image) -> np.ndarray:
        with torch.no_grad():
            tensor = self.preprocess(img).unsqueeze(0)
            features = self.model.encode_image(tensor)
            features = features / features.norm(dim=-1, keepdim=True)
            return features.cpu().numpy().astype(np.float32).flatten()

    def _save(self, path: Path, embed: np.ndarray) -> None:
        ext = path.suffix.lower()
        kind = "image" if ext in IMAGE_EXTS else "video"
        try:
            stat = path.stat()
        except OSError as e:
            log.warning(f"  stat failed для {path}: {e}")
            return
        existing = self.db.execute(
            "SELECT embed_idx FROM media WHERE path = ?", (str(path),)
        ).fetchone()
        if existing:
            embed_idx = int(existing[0])
            self.embeds[embed_idx] = embed
            self.db.execute(
                "UPDATE media SET file_size = ?, file_mtime = ?, indexed_at = ? WHERE path = ?",
                (stat.st_size, stat.st_mtime, time.time(), str(path)),
            )
        else:
            embed_idx = len(self.embeds)
            self.embeds = np.vstack([self.embeds, embed[np.newaxis, :]])
            self.db.execute(
                "INSERT INTO media (path, kind, embed_idx, file_size, file_mtime, indexed_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (str(path), kind, embed_idx, stat.st_size, stat.st_mtime, time.time()),
            )
        self.db.commit()

    def flush(self) -> None:
        """Сохраняет матрицу эмбеддингов на диск."""
        np.save(self.embeds_path, self.embeds)
        log.info(f"Эмбеддинги → {self.embeds_path} ({self.embeds.shape})")

    def close(self):
        self.db.close()
