"""
ChromaDB wrapper. Persists to disk so ingested documents survive restarts.
Handles collection lifecycle, adds, and similarity-search queries.
"""
from functools import lru_cache
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import get_settings
from app.core.logging_config import logger


class VectorStore:
    def __init__(self, persist_dir: str, collection_name: str):
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"Chroma collection '{collection_name}' ready ({self.collection.count()} chunks)")

    def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        self.collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)

    def query(self, query_embedding: List[float], top_k: int, where: Optional[Dict[str, Any]] = None):
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

    def list_sources(self) -> Dict[str, int]:
        data = self.collection.get(include=["metadatas"])
        counts: Dict[str, int] = {}
        for meta in data.get("metadatas", []):
            src = meta.get("source", "unknown")
            counts[src] = counts.get(src, 0) + 1
        return counts

    def delete_source(self, source: str) -> None:
        self.collection.delete(where={"source": source})

    def count(self) -> int:
        return self.collection.count()


@lru_cache
def get_vector_store() -> VectorStore:
    settings = get_settings()
    return VectorStore(settings.chroma_persist_dir, settings.collection_name)
