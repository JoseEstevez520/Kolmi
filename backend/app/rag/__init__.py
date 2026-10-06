"""Search by meaning: the pages cut into chunks, embedded and kept in `page_chunks` (pgvector),
found again with Supabase's hybrid search (full text and cosine, fused by rank).

Off until EMBEDDING_API_KEY is set: then nothing is indexed and `search` finds nothing, so the
chat and search_pages work as they did before.
"""

from .chunker import Chunk, chunk_markdown
from .embeddings import EMBEDDING_DIMENSIONS, Embedder, OpenAIEmbedder, get_embedder
from .index import index_page, index_pages, reindex_all, search

__all__ = [
    "Chunk",
    "chunk_markdown",
    "EMBEDDING_DIMENSIONS",
    "Embedder",
    "OpenAIEmbedder",
    "get_embedder",
    "index_page",
    "index_pages",
    "reindex_all",
    "search",
]
