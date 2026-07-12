import json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.core.logging_config import logger
from app.models.schemas import ChatRequest, ChatResponse
from app.services.rag_pipeline import answer_question, answer_question_stream

router = APIRouter(prefix="/api/chat", tags=["chat"])

SSE_HEADERS = {
    "Cache-Control": "no-cache, no-transform",
    "Connection": "keep-alive",
    # Prevents proxies like nginx from buffering the stream so tokens
    # arrive as they're generated rather than all at once at the end.
    "X-Accel-Buffering": "no",
}


def _sse_pack(event: str, data: dict, event_id: int) -> str:
    """Formats a single SSE message per spec: event/id/data lines, blank-line terminated."""
    return f"id: {event_id}\nevent: {event}\ndata: {json.dumps(data)}\n\n"


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest):
    answer, sources, latency_ms, cached = answer_question(request.message, request.top_k)
    return ChatResponse(
        answer=answer,
        sources=sources,
        session_id=request.session_id or "default",
        latency_ms=round(latency_ms, 1),
        cached=cached,
    )


@router.post("/stream")
async def chat_stream(request: ChatRequest, http_request: Request):
    """
    Server-Sent Events endpoint. Emits three named event types, in order:
      - "sources": retrieved chunks, sent once retrieval completes
      - "token":   incremental answer text as it streams from Groq
      - "done":    terminal event with final latency metadata
    On any failure, an "error" event is emitted so the client can recover
    gracefully instead of hanging on an open connection.
    """

    async def event_generator():
        event_id = 0
        try:
            for event in answer_question_stream(request.message, request.top_k):
                # stop generating if the client disconnected mid-stream
                if await http_request.is_disconnected():
                    logger.info("Client disconnected, stopping SSE stream")
                    break
                event_id += 1
                yield _sse_pack(event["type"], {"data": event["data"]}, event_id)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error while streaming chat response")
            event_id += 1
            yield _sse_pack("error", {"message": str(exc)}, event_id)

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers=SSE_HEADERS)
