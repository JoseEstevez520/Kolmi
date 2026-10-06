from __future__ import annotations

import hashlib
import logging
from typing import Any

from .chunker import chunk_markdown
from .embeddings import Embedder, get_embedder

log = logging.getLogger(__name__)

TABLE = "page_chunks"
# What of a chunk is embedded: a code block kept whole can outgrow the model's input (8,192
# tokens for OpenAI's); its start is enough to find it, and the chunk keeps all of it.
EMBED_CHARS = 16_000


def _hash(content_md: str) -> str:
    return hashlib.sha256(content_md.encode("utf-8")).hexdigest()


def index_page(
    client, node_id: int, content_md: str, embedder: Embedder, *, force: bool = False
) -> bool:
    """Put a page's chunks in `page_chunks`, in place of the ones it had. False when nothing
    changed: its chunks already carry the hash of this Markdown (unless `force`).

    The new chunks are embedded before the old ones go, so a failed call leaves the page as it
    was found. An empty page just loses its chunks.
    """
    content_md = content_md or ""
    if not content_md.strip():
        client.table(TABLE).delete().eq("node_id", node_id).execute()
        return False

    digest = _hash(content_md)
    if not force:
        rows = (
            client.table(TABLE).select("content_hash").eq("node_id", node_id).limit(1).execute().data
        )
        if rows and rows[0].get("content_hash") == digest:
            return False

    chunks = chunk_markdown(content_md)
    texts = [f"{c.heading}\n\n{c.content}"[:EMBED_CHARS] for c in chunks]
    vectors = embedder.embed(texts) if chunks else []
    client.table(TABLE).delete().eq("node_id", node_id).execute()
    if chunks:
        client.table(TABLE).insert(
            [
                {
                    "node_id": node_id,
                    "position": position,
                    "heading": chunk.heading,
                    "content": chunk.content,
                    "content_hash": digest,
                    "embedding": vector,
                }
                for position, (chunk, vector) in enumerate(zip(chunks, vectors))
            ]
        ).execute()
    return True


def _index_rows(
    client, rows: list[dict[str, Any]], embedder: Embedder, force: bool = False
) -> int:
    """Index each row ({id, content_md}); one that fails is logged and the rest go on."""
    indexed = 0
    for row in rows:
        try:
            if index_page(client, row["id"], row.get("content_md") or "", embedder, force=force):
                indexed += 1
        except Exception as exc:
            log.warning("could not index page %s: %s", row.get("id"), exc)
    return indexed


def index_pages(client, node_ids: list[int], embedder: Embedder | None = None) -> int:
    """Index these pages, as their Markdown is now; how many changed. Never raises: an index
    that fails must not fail the pass or the write that called it. Without an embedder (no
    EMBEDDING_API_KEY) it does nothing.
    """
    embedder = embedder or get_embedder()
    if embedder is None or not node_ids:
        return 0
    try:
        rows = (
            client.table("nodes")
            .select("id, content_md")
            .in_("id", list(node_ids))
            .execute()
            .data
        )
    except Exception as exc:
        log.warning("could not read pages %s to index them: %s", node_ids, exc)
        return 0
    return _index_rows(client, rows, embedder)


def reindex_all(client, embedder: Embedder | None = None, force: bool = False) -> int:
    """Index every page; how many changed. `force` embeds them all again, unchanged or not
    (after switching models). Without an embedder it does nothing.
    """
    embedder = embedder or get_embedder()
    if embedder is None:
        return 0
    rows = client.table("nodes").select("id, content_md").eq("kind", "page").execute().data
    return _index_rows(client, rows, embedder, force)


def search(client, query: str, k: int = 8, embedder: Embedder | None = None) -> list[dict]:
    """The `k` chunks closest to `query`, best first: {node_id, heading, content, score}.
    Full text and meaning together (match_page_chunks). Empty without an embedder or on any
    error, so the caller falls back to what it did before.
    """
    embedder = embedder or get_embedder()
    if embedder is None or not query.strip():
        return []
    try:
        [vector] = embedder.embed([query])
        rows = (
            client.rpc(
                "match_page_chunks",
                {"query_text": query, "query_embedding": vector, "match_count": k},
            )
            .execute()
            .data
        )
    except Exception as exc:
        log.warning("search by meaning failed: %s", exc)
        return []
    return [
        {
            "node_id": row["node_id"],
            "heading": row.get("heading") or "",
            "content": row.get("content") or "",
            "score": row.get("score"),
        }
        for row in rows or []
    ]
