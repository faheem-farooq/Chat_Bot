import hashlib
import math
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .models import DocumentChunk


EMBED_DIM = 256


def chunk_text(text: str, size: int = 900, overlap: int = 120) -> list[str]:
    clean = re.sub(r"\s+", " ", text).strip()
    chunks: list[str] = []
    start = 0
    while start < len(clean):
        chunks.append(clean[start : start + size])
        start += size - overlap
    return [chunk for chunk in chunks if chunk]


def embed_text(text: str) -> list[float]:
    vector = [0.0] * EMBED_DIM
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    for word in words:
        digest = hashlib.sha256(word.encode()).digest()
        index = int.from_bytes(digest[:2], "big") % EMBED_DIM
        sign = 1 if digest[2] % 2 == 0 else -1
        vector[index] += sign

    length = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / length for value in vector]


def add_document(db: Session, user_id: int, source_name: str, text: str) -> int:
    chunks = [
        DocumentChunk(
            user_id=user_id,
            source_name=source_name,
            content=chunk,
            embedding=embed_text(chunk),
        )
        for chunk in chunk_text(text)
    ]
    db.add_all(chunks)
    db.commit()
    return len(chunks)


def search_documents(db: Session, user_id: int, query: str, limit: int = 4) -> list[DocumentChunk]:
    embedding = embed_text(query)
    if settings.database_url.startswith("sqlite"):
        chunks = list(db.scalars(select(DocumentChunk).where(DocumentChunk.user_id == user_id)))
        chunks.sort(key=lambda chunk: cosine_distance(embedding, chunk.embedding))
        return chunks[:limit]

    stmt = (
        select(DocumentChunk)
        .where(DocumentChunk.user_id == user_id)
        .order_by(DocumentChunk.embedding.cosine_distance(embedding))
        .limit(limit)
    )
    return list(db.scalars(stmt))


def cosine_distance(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    return 1 - dot
