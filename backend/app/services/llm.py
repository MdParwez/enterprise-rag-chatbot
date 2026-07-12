"""
Groq LLM wrapper. Groq offers a free API tier with very low-latency inference
over open-weight models (Llama 3.x, etc.), which is why it's used here instead
of a paid provider.
"""
from functools import lru_cache
from typing import List, Dict, Iterator
from groq import Groq

from app.core.config import get_settings
from app.core.logging_config import logger

SYSTEM_PROMPT = """You are an enterprise knowledge assistant. Answer the user's question
using ONLY the provided context. If the answer is not contained in the context, say
you don't have enough information rather than guessing. Always be concise, precise,
and cite which source(s) you used by their [source] tag when relevant."""


class LLMService:
    def __init__(self, api_key: str, model: str, temperature: float, max_tokens: int):
        self.client = Groq(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def _build_messages(self, question: str, context: str) -> List[Dict[str, str]]:
        user_prompt = f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

    def generate(self, question: str, context: str) -> str:
        messages = self._build_messages(question, context)
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return completion.choices[0].message.content

    def generate_stream(self, question: str, context: str) -> Iterator[str]:
        messages = self._build_messages(question, context)
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta


@lru_cache
def get_llm_service() -> LLMService:
    s = get_settings()
    return LLMService(s.groq_api_key, s.groq_model, s.groq_temperature, s.groq_max_tokens)
