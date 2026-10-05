from __future__ import annotations

from typing import Any, Callable

# Shared by any agent that looks at the content tree before it answers (the gatekeeper, the
# chat): the tree as a short index, and a `read_page` tool so it reads only what it needs,
# instead of being handed the whole tree's content up front.

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
            line = f"{'  ' * depth}[{node['id']}] {node.get('kind')}: {node.get('title')}"
            # A short name (an acronym) says little on its own; its description says what it holds.
            description = (node.get("description") or "").strip()
            lines.append(f"{line} — {description}" if description else line)
            walk(node["id"], depth + 1)

    walk(None, 0)
    return "\n".join(lines) or "(empty: no sections or pages yet)"


def read_page_tool(
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
        names = ", ".join(f["name"] for f in page.get("files") or [])
        attached = f"\n\nFiles: {names}" if names else ""
        return (
            f"Page {node_id}, {node.get('title')}:\n\n{markdown or '(this page is still empty)'}"
            f"{attached}"
        )

    return run
