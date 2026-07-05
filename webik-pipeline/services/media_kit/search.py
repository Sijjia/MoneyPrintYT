"""
services/media_kit/search.py
Семантический поиск по CLIP-индексу медиатеки.

Использование:
    s = MediaSearch(index_dir=Path(".media_index"))
    s.load_model()
    results = s.search("korean shaman ritual", k=5, min_score=0.20)
    for path, score in results:
        print(f"{score:.3f} {path}")

Алгоритм:
1. text query → CLIP text embed (normalized 512-dim)
2. cosine similarity vs все image-embeds в индексе
3. top-K по убыванию, фильтр min_score
"""
import sqlite3
from pathlib import Path
from typing import List, Tuple

import numpy as np
import open_clip
import torch

from core.logger import setup_logger
from services.media_kit.indexer import MODEL_NAME, MODEL_PRETRAINED

log = setup_logger("search")


class MediaSearch:
    def __init__(self, index_dir: Path):
        self.index_dir = Path(index_dir)
        self.db_path = self.index_dir / "db.sqlite"
        self.embeds_path = self.index_dir / "embeds.npy"
        self.model = None
        self.tokenizer = None
        self.embeds = None
        self.paths: List[str] = []
        self.kinds: List[str] = []

    def _load_index(self) -> bool:
        if not self.db_path.exists() or not self.embeds_path.exists():
            log.warning(f"Индекс не найден в {self.index_dir} — сначала прогони `webik.py index`")
            return False
        self.embeds = np.load(self.embeds_path)
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT path, kind, embed_idx FROM media ORDER BY embed_idx"
        ).fetchall()
        conn.close()
        self.paths = [r[0] for r in rows]
        self.kinds = [r[1] for r in rows]
        return True

    def load_model(self):
        if self.model is not None:
            return
        log.info(f"Загружаю CLIP {MODEL_NAME} ({MODEL_PRETRAINED})...")
        self.model, _, _ = open_clip.create_model_and_transforms(
            MODEL_NAME, pretrained=MODEL_PRETRAINED
        )
        self.tokenizer = open_clip.get_tokenizer(MODEL_NAME)
        self.model.eval()

    def _encode_text(self, query: str) -> np.ndarray:
        with torch.no_grad():
            tokens = self.tokenizer([query])
            features = self.model.encode_text(tokens)
            features = features / features.norm(dim=-1, keepdim=True)
            return features.cpu().numpy().astype(np.float32).flatten()

    def search(
        self,
        query: str,
        k: int = 5,
        min_score: float = 0.20,
        kind_filter: str = "any",
    ) -> List[Tuple[str, float, str]]:
        """Возвращает top-K (path, score, kind), отсортированные по score убыв.

        Args:
            kind_filter: "any" | "image" | "video"
            min_score: cosine similarity threshold (0..1). Webik queries обычно
                дают 0.20-0.35 для релевантного, <0.18 — нерелевантно.
        """
        if not self._load_index():
            return []
        if len(self.paths) == 0:
            return []
        self.load_model()
        query_embed = self._encode_text(query)
        # Embeds уже нормализованы → dot product = cosine similarity
        sims = self.embeds @ query_embed
        top_indices = np.argsort(-sims)
        results: List[Tuple[str, float, str]] = []
        for idx in top_indices:
            score = float(sims[idx])
            if score < min_score:
                break
            kind = self.kinds[idx]
            if kind_filter != "any" and kind != kind_filter:
                continue
            results.append((self.paths[idx], score, kind))
            if len(results) >= k:
                break
        return results
