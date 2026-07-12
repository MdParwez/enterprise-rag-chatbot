"""
Enterprise RAG Chatbot - FastAPI entrypoint.
Wires together config, logging, CORS, and the chat / documents / evaluation routers.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging_config import configure_logging, logger
from app.api.routes import chat, documents, evaluation, health

configure_logging()
settings = get_settings()

app = FastAPI(
    title="Enterprise RAG Chatbot API",
    description="FastAPI + ChromaDB + Groq + RAGAS powered retrieval-augmented chatbot",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(evaluation.router)


@app.on_event("startup")
def on_startup():
    logger.info("Enterprise RAG Chatbot API starting up...")
