from fastapi import APIRouter
from app.services.vectorstore import get_vector_store

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    store = get_vector_store()
    return {"status": "ok", "chunks_indexed": store.count()}
