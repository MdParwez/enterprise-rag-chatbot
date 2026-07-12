"""
Recursive text chunker (no heavyweight langchain dependency).
Splits on paragraph -> sentence -> word boundaries, preserving overlap
so that context is not lost at chunk edges. This is a key RAG quality lever.
"""
from typing import List

SEPARATORS = ["\n\n", "\n", ". ", " "]


def _split(text: str, separators: List[str]) -> List[str]:
    if not separators:
        return [text]
    sep, rest = separators[0], separators[1:]
    if sep not in text:
        return _split(text, rest)
    return [p for p in text.split(sep) if p.strip()]


def chunk_text(text: str, chunk_size: int = 800, chunk_overlap: int = 120) -> List[str]:
    text = text.strip()
    if not text:
        return []

    pieces = _split(text, SEPARATORS)
    chunks: List[str] = []
    current = ""

    for piece in pieces:
        candidate = f"{current} {piece}".strip() if current else piece
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                chunks.append(current)
            # start next chunk with overlap from the tail of the previous chunk
            overlap_text = current[-chunk_overlap:] if current else ""
            current = f"{overlap_text} {piece}".strip()
            # if a single piece is still too large, hard-split it
            while len(current) > chunk_size:
                chunks.append(current[:chunk_size])
                current = current[chunk_size - chunk_overlap:]

    if current:
        chunks.append(current)

    return chunks
