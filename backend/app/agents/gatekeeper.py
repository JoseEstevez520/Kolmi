from __future__ import annotations

import json
import logging
from typing import Any

from ..class_settings import FALLBACK_LANGUAGE
from .client import LLM
from .prompts import gatekeeper_system
from .schemas import GatekeeperResult
from .tree import READ_PAGE_TOOL, PageReader, build_index, read_page_tool

log = logging.getLogger(__name__)

__all__ = ["run_gatekeeper", "build_index", "READ_PAGE_TOOL", "PageReader"]


def _file(file: dict[str, Any]) -> dict[str, Any]:
    out = {
        "id": file["id"],
        "name": file["name"],
        "kind": file.get("kind"),
        "size": file.get("size"),
    }
    if file.get("peek"):
        out["peek"] = file["peek"]
    return out


def _notes(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    notes = []
    for row in rows:
        note = {"id": row["id"], "content": row["content"], "hint": row.get("node_id")}
        if row.get("files"):
            note["files"] = [_file(f) for f in row["files"]]
        notes.append(note)
    return notes


def _payload(notes: list[dict[str, Any]], nodes: list[dict[str, Any]]) -> str:
    return (
        f"Tree:\n{build_index(nodes)}\n\n"
        f"Notes:\n{json.dumps(_notes(notes), ensure_ascii=False, indent=1)}"
    )


def run_gatekeeper(
    llm: LLM,
    notes: list[dict[str, Any]],
    nodes: list[dict[str, Any]],
    *,
    read_page: PageReader | None = None,
    language: str = FALLBACK_LANGUAGE,
) -> GatekeeperResult:
    """Review the pending notes: what adds something new to the class's notes, and where.

    It sees the tree as an index and reads the pages it wants with the `read_page` tool
    (`read_page` gives a page's row). With a model that has no tools, or if that loop fails,
    it answers from the index alone. Its summaries come in the class `language`, whatever
    language each note was written in. The result's `reads` lists what it read.
    """
    system = gatekeeper_system(language)
    user = _payload(notes, nodes)

    with_tools = getattr(llm, "complete_with_tools", None)
    if with_tools is not None and read_page is not None:
        reads: list[int] = []
        try:
            raw = with_tools(system, user, [READ_PAGE_TOOL], read_page_tool(nodes, read_page, reads))
            plan = GatekeeperResult.model_validate(raw)
            plan.reads = reads
            return plan
        except Exception as exc:  # the pass goes on without the tools
            log.warning("gatekeeper tool loop failed, answering from the index: %s", exc)

    raw = llm.complete_json(system, user)
    return GatekeeperResult.model_validate(raw)
