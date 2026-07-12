"""
Centralized application settings.
All values are overridable via environment variables or a .env file.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Groq LLM ---
    groq_api_key: str = "your_groq_api_key_here"
    groq_model: str = "llama-3.3-70b-versatile"
    groq_temperature: float = 0.2
    groq_max_tokens: int = 1024

    # --- Embeddings (local, free) ---
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # --- ChromaDB ---
    chroma_persist_dir: str = "./chroma_data"
    collection_name: str = "enterprise_rag"

    # --- Chunking strategy ---
    chunk_size: int = 800
    chunk_overlap: int = 120

    # --- Retrieval / optimization ---
    top_k: int = 5
    similarity_threshold: float = 0.25

    # --- Query cache (reduces duplicate LLM + retrieval calls) ---
    cache_ttl_seconds: int = 300
    cache_max_size: int = 256

    # --- CORS ---
    cors_origins: str = "http://localhost:5173,http://localhost:5174,http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
