"""
Core RAG orchestration: embed query -> retrieve from Chroma -> filter by
similarity threshold -> build grounded prompt -> call Groq -> return answer
with cited sources. Includes the query cache optimization.
"""
import time
from typing import List, Tuple
from app.core.config import get_settings
from app.core.logging_config import logger
from app.models.schemas import SourceChunk
from app.services.embeddings import get_embedding_service
from app.services.vectorstore import get_vector_store
from app.services.llm import get_llm_service
from app.services import cache


def _retrieve(question: str, top_k: int) -> List[SourceChunk]:
    settings = get_settings()
    embedder = get_embedding_service()
    store = get_vector_store()
    logger.info(f"Retrieval request: question='{question[:120]}', top_k={top_k}")

    query_vec = embedder.embed_query(question)
    results = store.query(query_vec, top_k=top_k)

    sources: List[SourceChunk] = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for doc, meta, dist in zip(docs, metas, distances):
        similarity = 1 - dist  # cosine distance -> similarity
        if similarity < settings.similarity_threshold:
            continue
        sources.append(SourceChunk(
            chunk_id=meta.get("source", "") + str(meta.get("page", "")),
            source=meta.get("source", "unknown"),
            page=meta.get("page") if meta.get("page", -1) != -1 else None,
            text=doc,
            score=round(similarity, 4),
        ))
    logger.info(f"Retrieved {len(sources)} source(s) (similarity_threshold={settings.similarity_threshold})")
    return sources


def _build_context(sources: List[SourceChunk]) -> str:
    parts = []
    for s in sources:
        page_info = f" p.{s.page}" if s.page else ""
        parts.append(f"[{s.source}{page_info}]\n{s.text}")
    return "\n\n---\n\n".join(parts)


def answer_question(question: str, top_k: int | None = None) -> Tuple[str, List[SourceChunk], float, bool]:
    """Returns (answer, sources, latency_ms, was_cached)."""
    settings = get_settings()
    k = top_k or settings.top_k
    start = time.perf_counter()

    cached = cache.get_cached(question, k)
    if cached:
        latency = (time.perf_counter() - start) * 1000
        answer, sources = cached
        return answer, sources, latency, True

    sources = _retrieve(question, k)
    if not sources:
        latency = (time.perf_counter() - start) * 1000
        return ("I don't have enough information in the knowledge base to answer that.", [], latency, False)

    context = _build_context(sources)
    llm = get_llm_service()
    answer = llm.generate(question, context)

    cache.set_cached(question, k, (answer, sources))
    latency = (time.perf_counter() - start) * 1000
    logger.info(f"Answered in {latency:.1f}ms using {len(sources)} chunks")
    return answer, sources, latency, False


def answer_question_stream(question: str, top_k: int | None = None):
    """Generator version for SSE streaming. Sources are retrieved first,
    then tokens are streamed as they arrive from Groq."""
    settings = get_settings()
    k = top_k or settings.top_k
    start = time.perf_counter()
    sources = _retrieve(question, k)

    if not sources:
        yield {"type": "sources", "data": []}
        yield {"type": "token", "data": "I don't have enough information in the knowledge base to answer that."}
        yield {"type": "done", "data": {"latency_ms": round((time.perf_counter() - start) * 1000, 1)}}
        return

    yield {"type": "sources", "data": [s.model_dump() for s in sources]}

    context = _build_context(sources)
    llm = get_llm_service()
    for token in llm.generate_stream(question, context):
        yield {"type": "token", "data": token}

    yield {"type": "done", "data": {"latency_ms": round((time.perf_counter() - start) * 1000, 1)}}
