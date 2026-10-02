from __future__ import annotations

import json
import re
from typing import Any

from ..class_settings import FALLBACK_LANGUAGE
from .client import LLM
from .prompts import gatekeeper_system
from .schemas import GatekeeperResult

TREE_FIELDS = ("id", "parent_id", "kind", "title", "description")

# How much of a page's Markdown the gatekeeper sees, to tell a new note from a repeat: its
# opening and headings for every page, and its start for a page a note points at.
OUTLINE_CHARS = 600
HINTED_CHARS = 4000


def _outline(markdown: str) -> str:
    """A page's opening paragraph and its headings, short."""
    blocks = [b.strip() for b in markdown.split("\n\n") if b.strip()]
    opening = next((b for b in blocks if not b.startswith("#")), "")
    headings = re.findall(r"^#{2,3} .+$", markdown, re.M)
    return "\n".join([opening, *headings])[:OUTLINE_CHARS]


def _tree(rows: list[dict[str, Any]], hinted: set[int]) -> list[dict[str, Any]]:
    tree = []
    for row in rows:
        item = {field: row.get(field) for field in TREE_FIELDS}
        markdown = (row.get("content_md") or "").strip()
        if markdown:
            item["excerpt"] = (
                markdown[:HINTED_CHARS] if row.get("id") in hinted else _outline(markdown)
            )
        tree.append(item)
    return tree


def _notes(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"id": row["id"], "content": row["content"], "node_id": row.get("node_id")}
        for row in rows
    ]


def run_gatekeeper(
    llm: LLM,
    notes: list[dict[str, Any]],
    nodes: list[dict[str, Any]],
    *,
    language: str = FALLBACK_LANGUAGE,
) -> GatekeeperResult:
    """Review the pending notes: what adds something new to the class's notes, and where.

    Its summaries come in the class `language`, whatever language each note was written in.
    """
    hinted = {row.get("node_id") for row in notes}
    payload = {"tree": _tree(nodes, hinted), "notes": _notes(notes)}
    raw = llm.complete_json(
        gatekeeper_system(language), json.dumps(payload, ensure_ascii=False)
    )
    return GatekeeperResult.model_validate(raw)
