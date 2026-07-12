"""
Document ingestion pipeline: extract text from pdf/docx/txt, chunk it,
embed the chunks in a single batch call, and upsert into ChromaDB.
"""
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

from pypdf import PdfReader
from docx import Document as DocxDocument

from app.core.config import get_settings
from app.core.logging_config import logger
from app.services.chunking import chunk_text
from app.services.embeddings import get_embedding_service
from app.services.vectorstore import get_vector_store


def _extract_text(file_path: Path) -> List[Dict[str, Any]]:
    """Returns a list of {text, page} dicts so page numbers can be kept as metadata."""
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        reader = PdfReader(str(file_path))
        return [{"text": page.extract_text() or "", "page": i + 1} for i, page in enumerate(reader.pages)]

    if suffix == ".docx":
        doc = DocxDocument(str(file_path))
        full_text = "\n".join(p.text for p in doc.paragraphs)
        return [{"text": full_text, "page": None}]

    # plain text / markdown fallback
    return [{"text": file_path.read_text(errors="ignore"), "page": None}]


def ingest_file(file_path: Path, source_name: str | None = None) -> int:
    """Ingests a single file into the vector store. Returns number of chunks added.

    Args:
        file_path: path to the temporary file on disk
        source_name: optional original filename to use in metadata (prevents leaking temp filenames)
    """
    settings = get_settings()
    embedder = get_embedding_service()
    store = get_vector_store()

    pages = _extract_text(file_path)
    all_chunks: List[str] = []
    all_meta: List[Dict[str, Any]] = []

    for page in pages:
        for chunk in chunk_text(page["text"], settings.chunk_size, settings.chunk_overlap):
            all_chunks.append(chunk)
            all_meta.append({
                "source": source_name or file_path.name,
                "page": page["page"] if page["page"] is not None else -1,
                "ingested_at": datetime.now(timezone.utc).isoformat(),
            })

    if not all_chunks:
        logger.warning(f"No extractable text found in {file_path.name}")
        return 0

    embeddings = embedder.embed_texts(all_chunks).tolist()
    # Use the provided source_name (without extension) when generating ids where possible
    id_stem = Path(source_name).stem if source_name else file_path.stem
    ids = [f"{id_stem}_{uuid.uuid4().hex[:8]}_{i}" for i in range(len(all_chunks))]

    store.add(ids=ids, embeddings=embeddings, documents=all_chunks, metadatas=all_meta)
    logger.info(f"Ingested {len(all_chunks)} chunks from {file_path.name}")
    return len(all_chunks)
