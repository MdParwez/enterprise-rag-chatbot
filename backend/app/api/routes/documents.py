import shutil
import tempfile
from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.core.logging_config import logger
from app.models.schemas import IngestResponse, DocumentInfo
from app.services.ingestion import ingest_file
from app.services.vectorstore import get_vector_store
from app.services import cache as query_cache

router = APIRouter(prefix="/api/documents", tags=["documents"])
ALLOWED_SUFFIXES = {".pdf", ".docx", ".txt", ".md"}


@router.post("/upload", response_model=IngestResponse)
async def upload_documents(files: List[UploadFile] = File(...)):
    total_chunks = 0
    docs_info = []

    for upload in files:
        suffix = Path(upload.filename).suffix.lower()
        if suffix not in ALLOWED_SUFFIXES:
            raise HTTPException(400, f"Unsupported file type: {upload.filename}")

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(upload.file, tmp)
            tmp_path = Path(tmp.name)

        try:
            # Pass original filename so metadata records the uploaded name instead of a temp name
            n_chunks = ingest_file(tmp_path, source_name=upload.filename)
            total_chunks += n_chunks
        finally:
            tmp_path.unlink(missing_ok=True)

    # Index changed -> clear query cache to avoid stale answers
    try:
        query_cache.clear_cache()
    except Exception:
        logger.exception("Failed to clear query cache after ingestion")

    store = get_vector_store()
    sources = store.list_sources()
    for name, count in sources.items():
        docs_info.append(DocumentInfo(source=name, chunks=count, ingested_at=""))

    return IngestResponse(documents=docs_info, total_chunks_added=total_chunks)


@router.get("", response_model=List[DocumentInfo])
def list_documents():
    store = get_vector_store()
    sources = store.list_sources()
    return [DocumentInfo(source=name, chunks=count, ingested_at="") for name, count in sources.items()]


@router.delete("/{source_name}")
def delete_document(source_name: str):
    store = get_vector_store()
    store.delete_source(source_name)
    return {"deleted": source_name}
