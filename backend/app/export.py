"""Export the class's pages as Markdown files, one per page, folders mirroring the tree.

The Markdown is the page's source (`content_md`, what the notes agent writes); the web page is
drawn from it afterwards. So an export reads what is stored and packs it: no model, no cost.

Links and images in that Markdown were often written for the class repo's files (`../modelos/`,
`scopes-y-estado.md`) and mean nothing here. The export keeps what still works (external links,
anchors, links to another page that is in the export, rewritten to its file) and turns the rest
into plain text, so no file points at nothing.
"""

from __future__ import annotations

import io
import posixpath
import re
import unicodedata
import zipfile
from typing import Any

FENCE = re.compile(r"(```.*?```|~~~.*?~~~)", re.S)
IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)\s]*)[^)]*\)")
LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)[^)]*\)")
NODE_LINK = re.compile(r"^/node/(\d+)(#.*)?$")
EXTERNAL = ("http://", "https://", "mailto:", "tel:")


def slugify(text: str, fallback: str = "page") -> str:
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", plain.lower()).strip("-")[:60].strip("-")
    return slug or fallback


def _children(nodes: list[dict[str, Any]]) -> dict[int | None, list[dict[str, Any]]]:
    ids = {node["id"] for node in nodes}
    tree: dict[int | None, list[dict[str, Any]]] = {}
    for node in nodes:
        parent = node.get("parent_id") if node.get("parent_id") in ids else None
        tree.setdefault(parent, []).append(node)
    for siblings in tree.values():
        siblings.sort(key=lambda n: (n.get("position") or 0, n["id"]))
    return tree


def _has_content(node: dict[str, Any]) -> bool:
    return node.get("kind") == "page" and bool((node.get("content_md") or "").strip())


def plan(nodes: list[dict[str, Any]], scope: int | None = None) -> dict[int, tuple[str, list[str]]]:
    """Each exported page's path in the zip and the titles of the sections above it.

    A page with no Markdown is left out. Siblings are numbered in the order the admin gave them,
    so the order survives in any file manager. With a `scope` (a section, or a page), the paths
    start at it; without, at the top level.
    """
    tree = _children(nodes)
    by_id = {node["id"]: node for node in nodes}
    if scope is not None and scope not in by_id:
        raise KeyError(scope)
    out: dict[int, tuple[str, list[str]]] = {}

    def folders_has_pages(node: dict[str, Any]) -> bool:
        if _has_content(node):
            return True
        return any(folders_has_pages(child) for child in tree.get(node["id"], []))

    def walk(siblings: list[dict[str, Any]], folder: str, trail: list[str]) -> None:
        kept = [node for node in siblings if folders_has_pages(node)]
        width = max(2, len(str(len(kept))))
        for index, node in enumerate(kept, 1):
            name = f"{str(index).zfill(width)}-{slugify(node['title'], str(node['id']))}"
            if node["kind"] == "page":
                out[node["id"]] = (posixpath.join(folder, name + ".md"), trail)
            else:
                walk(tree.get(node["id"], []), posixpath.join(folder, name), [*trail, node["title"]])

    if scope is None:
        walk(tree.get(None, []), "", [])
    else:
        root = by_id[scope]
        if root["kind"] == "page":
            if _has_content(root):
                out[root["id"]] = (slugify(root["title"], str(root["id"])) + ".md", [])
        else:
            walk(tree.get(root["id"], []), "", [])
    return out


def rewrite(markdown: str, here: str, paths: dict[int, str], titles: dict[str, int]) -> str:
    """The page's Markdown with every link and image made to work, or to plain text."""

    def target(node_id: int) -> str | None:
        path = paths.get(node_id)
        return posixpath.relpath(path, posixpath.dirname(here) or ".") if path else None

    def image(match: re.Match[str]) -> str:
        alt, url = match.group(1), match.group(2)
        if url.startswith(EXTERNAL):
            return match.group(0)
        return alt  # a file that only existed beside the original: its description is what is left

    def link(match: re.Match[str]) -> str:
        label, url = match.group(1), match.group(2)
        if url.startswith(EXTERNAL) or url.startswith("#"):
            return match.group(0)
        node_id = None
        node_link = NODE_LINK.match(url)
        if node_link:
            node_id = int(node_link.group(1))
        elif label.strip().lower() in titles:
            node_id = titles[label.strip().lower()]
        relative = target(node_id) if node_id is not None else None
        return f"[{label}]({relative})" if relative else label

    parts = FENCE.split(markdown)
    for i in range(0, len(parts), 2):  # the odd parts are code, which stays as written
        parts[i] = LINK.sub(link, IMAGE.sub(image, parts[i]))
    return "".join(parts)


def render_page(node: dict[str, Any], trail: list[str], body: str) -> str:
    """Title as the heading, where the page sits as plain text, then its Markdown."""
    title = node["title"].strip()
    body = body.strip()
    first = body.splitlines()[0].strip() if body else ""
    if first.startswith("# ") and first[2:].strip().lower() == title.lower():
        body = "\n".join(body.splitlines()[1:]).strip()
    where = " > ".join(trail)
    head = f"# {title}\n\n" + (f"{where}\n\n" if where else "")
    return head + body + "\n"


def build(nodes: list[dict[str, Any]], scope: int | None = None) -> dict[str, str]:
    """Path in the zip -> file text, for the pages under `scope` (all of them without one)."""
    layout = plan(nodes, scope)
    paths = {node_id: path for node_id, (path, _) in layout.items()}
    by_id = {node["id"]: node for node in nodes}
    titles: dict[str, int] = {}
    for node_id in layout:
        titles.setdefault(by_id[node_id]["title"].strip().lower(), node_id)
    files: dict[str, str] = {}
    for node_id, (path, trail) in layout.items():
        node = by_id[node_id]
        body = rewrite(node.get("content_md") or "", path, paths, titles)
        files[path] = render_page(node, trail, body)
    return files


def to_zip(files: dict[str, str]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path, text in sorted(files.items()):
            archive.writestr(path, text)
    return buffer.getvalue()
