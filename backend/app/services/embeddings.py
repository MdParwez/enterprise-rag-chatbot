"""
Local, free embedding model wrapper (sentence-transformers).
Loaded once as a singleton to avoid reloading weights on every request -
this is one of the key latency optimizations in this project.
"""
from functools import lru_cache
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import get_settings
from app.core.logging_config import logger


class EmbeddingService:
    def __init__(self, model_name: str):
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        # batch encoding is significantly faster than one-by-one calls
        return self.model.encode(texts, batch_size=32, show_progress_bar=False, normalize_embeddings=True)

    def embed_query(self, text: str) -> List[float]:
        return self.model.encode(text, normalize_embeddings=True).tolist()


@lru_cache
def get_embedding_service() -> EmbeddingService:
    settings = get_settings()
    return EmbeddingService(settings.embedding_model)
