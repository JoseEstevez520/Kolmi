from __future__ import annotations

import json
from typing import Any

from ..class_settings import FALLBACK_LANGUAGE
from .client import LLM
from .prompts import gatekeeper_system
from .schemas import GatekeeperResult

TREE_FIELDS = ("id", "parent_id", "kind", "title", "description")


def _tree(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{field: row.get(field) for field in TREE_FIELDS} for row in rows]


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
    """Review the pending notes and decide what goes in, and where.

    Its summaries come in the class `language`, whatever language each note was written in.
    """
    payload = {"tree": _tree(nodes), "notes": _notes(notes)}
    raw = llm.complete_json(
        gatekeeper_system(language), json.dumps(payload, ensure_ascii=False)
    )
    return GatekeeperResult.model_validate(raw)
