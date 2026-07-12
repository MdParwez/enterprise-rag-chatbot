"""Pydantic request/response contracts shared across API routes."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SourceChunk(BaseModel):
    chunk_id: str
    source: str
    page: Optional[int] = None
    text: str
    score: float


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: Optional[str] = "default"
    top_k: Optional[int] = None
    stream: bool = False


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceChunk]
    session_id: str
    latency_ms: float
    cached: bool = False


class DocumentInfo(BaseModel):
    source: str
    chunks: int
    ingested_at: str


class IngestResponse(BaseModel):
    documents: List[DocumentInfo]
    total_chunks_added: int


class EvalItem(BaseModel):
    question: str
    ground_truth: Optional[str] = None


class EvalRequest(BaseModel):
    items: Optional[List[EvalItem]] = None  # if omitted, uses eval/test_dataset.json


class EvalResponse(BaseModel):
    scores: Dict[str, float]
    per_question: List[Dict[str, Any]]
    n_items: int
