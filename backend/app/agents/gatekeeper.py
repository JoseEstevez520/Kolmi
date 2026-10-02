from __future__ import annotations

import json
import logging
from typing import Any, Callable

from ..class_settings import FALLBACK_LANGUAGE
from .client import LLM
from .prompts import gatekeeper_system
from .schemas import GatekeeperResult

log = logging.getLogger(__name__)

READ_PAGE_TOOL = {
    "type": "function",
    "function": {
        "name": "read_page",
        "description": "Read a node of the tree: a page's whole Markdown, or what hangs from a section.",
        "parameters": {
            "type": "object",
            "properties": {"node_id": {"type": "integer", "description": "The node's id."}},
            "required": ["node_id"],
        },
    },
}

PageReader = Callable[[int], dict[str, Any] | None]


def build_index(nodes: list[dict[str, Any]]) -> str:
    """The tree as a short index, like `ls -R`: one line per node, indented by depth."""
    ids = {node["id"] for node in nodes}
    children: dict[int | None, list[dict[str, Any]]] = {}
    for node in nodes:
        parent = node.get("parent_id") if node.get("parent_id") in ids else None
        children.setdefault(parent, []).append(node)

    lines: list[str] = []

    def walk(parent: int | None, depth: int) -> None:
        for node in sorted(children.get(parent, []), key=lambda n: n.get("position") or 0):
            lines.append(f"{'  ' * depth}[{node['id']}] {node.get('kind')}: {node.get('title')}")
            walk(node["id"], depth + 1)

    walk(None, 0)
    return "\n".join(lines) or "(empty: no sections or pages yet)"


def _notes(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"id": row["id"], "content": row["content"], "hint": row.get("node_id")}
        for row in rows
    ]


def _payload(notes: list[dict[str, Any]], nodes: list[dict[str, Any]]) -> str:
    return (
        f"Tree:\n{build_index(nodes)}\n\n"
        f"Notes:\n{json.dumps(_notes(notes), ensure_ascii=False, indent=1)}"
    )


def _reader(
    nodes: list[dict[str, Any]], read_page: PageReader, reads: list[int]
) -> Callable[[str, dict[str, Any]], str]:
    """The `read_page` tool: a page's Markdown, or a section's children. Each read goes in `reads`."""
    by_id = {node["id"]: node for node in nodes}

    def run(name: str, args: dict[str, Any]) -> str:
        if name != "read_page":
            return f"There is no tool called {name}."
        try:
            node_id = int(args.get("node_id"))
        except (TypeError, ValueError):
            return "read_page needs a node_id, a number from the index."
        node = by_id.get(node_id)
        if node is None:
            return f"There is no node {node_id} in the tree."
        reads.append(node_id)
        if node.get("kind") == "section":
            kids = [n for n in nodes if n.get("parent_id") == node_id]
            listing = "\n".join(f"[{n['id']}] {n.get('kind')}: {n.get('title')}" for n in kids)
            return f"Section {node_id}, {node.get('title')}:\n{listing or '(empty)'}"
        page = read_page(node_id) or {}
        markdown = (page.get("content_md") or "").strip()
        return f"Page {node_id}, {node.get('title')}:\n\n{markdown or '(this page is still empty)'}"

    return run


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
            raw = with_tools(system, user, [READ_PAGE_TOOL], _reader(nodes, read_page, reads))
            plan = GatekeeperResult.model_validate(raw)
            plan.reads = reads
            return plan
        except Exception as exc:  # the pass goes on without the tools
            log.warning("gatekeeper tool loop failed, answering from the index: %s", exc)

    raw = llm.complete_json(system, user)
    return GatekeeperResult.model_validate(raw)
