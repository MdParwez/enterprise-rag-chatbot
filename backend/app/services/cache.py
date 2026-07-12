"""
TTL + LRU query cache. Repeated or near-duplicate questions (common in
enterprise support/chat scenarios) skip both retrieval and LLM generation,
cutting latency and Groq token usage significantly.
"""
import hashlib
from cachetools import TTLCache
from app.core.config import get_settings

_settings = get_settings()
_cache = TTLCache(maxsize=_settings.cache_max_size, ttl=_settings.cache_ttl_seconds)


def _key(question: str, top_k: int) -> str:
    return hashlib.sha256(f"{question.strip().lower()}::{top_k}".encode()).hexdigest()


def get_cached(question: str, top_k: int):
    return _cache.get(_key(question, top_k))


def set_cached(question: str, top_k: int, value) -> None:
    _cache[_key(question, top_k)] = value


def clear_cache() -> None:
    """Clears the entire query cache. Call after ingestion or when the index changes."""
    _cache.clear()
