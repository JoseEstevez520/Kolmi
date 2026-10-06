from __future__ import annotations

from functools import lru_cache
from typing import Protocol

from ..config import get_settings

# The size of `page_chunks.embedding`. It is sent as `dimensions`, so a model whose vectors are
# longer (text-embedding-3-large) shortens them to fit the column.
EMBEDDING_DIMENSIONS = 1536

# Inputs per request: the API takes up to 2048, fewer keeps each request small.
BATCH_SIZE = 100


class Embedder(Protocol):
    """Texts to vectors, one per text and in the same order. Swapped for a fake in tests."""

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class OpenAIEmbedder:
    """Any OpenAI-compatible embeddings endpoint; OpenAI's by default."""

    def __init__(self, *, api_key: str, base_url: str, model: str) -> None:
        from openai import OpenAI

        self.model = model
        self._client = OpenAI(api_key=api_key, base_url=base_url)

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), BATCH_SIZE):
            response = self._client.embeddings.create(
                model=self.model,
                input=texts[start : start + BATCH_SIZE],
                dimensions=EMBEDDING_DIMENSIONS,
            )
            vectors += [item.embedding for item in sorted(response.data, key=lambda d: d.index)]
        return vectors


@lru_cache
def get_embedder() -> Embedder | None:
    """The embedder, when EMBEDDING_API_KEY is set; without it, search by meaning is off."""
    settings = get_settings()
    if not settings.embedding_api_key:
        return None
    return OpenAIEmbedder(
        api_key=settings.embedding_api_key,
        base_url=settings.embedding_base_url,
        model=settings.embedding_model,
    )
