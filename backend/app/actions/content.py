from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field

from ..auth import Context
from ..files import node_files
from ..store import place_among
from .registry import action


class ViewNodeParams(BaseModel):
    node_id: int = Field(..., description="The node's id, from list_nodes.")
    include_web: bool = Field(
        False,
        description="Also give a page's web, its OpenUI Lang as the app draws it, to change what is there with write_page_web. It is long: leave it out to read the page.",
    )


class CreateNodeParams(BaseModel):
    parent_id: int | None = Field(None, description="The section it goes in; null for the top level.")
    kind: Literal["section", "page"] = Field(..., description="section groups other nodes; page holds content.")
    title: str = Field(..., description="Short, as the sidebar shows it.")
    description: str | None = Field(None, description="One line on what it covers. The AI reads it to decide where notes go.")
    icon: str | None = Field(None, description="A Lucide icon name, such as BookOpen; null for none.")
    color: str | None = Field(None, description="Its colour: \"\" for the app's grey, or one of #2563eb (blue), #0d9488 (teal), #7c3aed (violet), #d97706 (amber), #c026d3 (fuchsia), #65a30d (lime), #e11d48 (rose).")
    on_home: bool | None = Field(None, description="Whether it shows on the home screen.")


class UpdateNodeParams(BaseModel):
    # A page's content is the daily pass's to write, not an edit: sending it is refused.
    model_config = ConfigDict(extra="forbid")

    node_id: int = Field(..., description="The node to change, from list_nodes.")
    title: str | None = Field(None, description="New title, as the sidebar shows it.")
    description: str | None = Field(None, description="New one-line description. The AI reads it to decide where notes go.")
    icon: str | None = Field(None, description="A Lucide icon name, such as BookOpen.")
    color: str | None = Field(None, description="Its colour: \"\" for the app's grey, or one of #2563eb (blue), #0d9488 (teal), #7c3aed (violet), #d97706 (amber), #c026d3 (fuchsia), #65a30d (lime), #e11d48 (rose).")
    on_home: bool | None = Field(None, description="Whether it shows on the home screen.")


class MoveNodeParams(BaseModel):
    node_id: int = Field(..., description="The node to move, from list_nodes.")
    parent_id: int | None = Field(None, description="Its parent after the move; null for the top level. Left out, it stays under the one it has, to only reorder.")
    # Where among the new siblings. Left out, only the parent changes (the web moves, then
    # reorders).
    placement: Literal["first", "after", "last"] | None = Field(None, description="Where among its new siblings: first, after (with after_node_id) or last.")
    after_node_id: int | None = Field(None, description="With placement after: the sibling it goes right after.")


class ReorderNodesParams(BaseModel):
    ids: list[int]


class NodeIdParams(BaseModel):
    node_id: int = Field(..., description="The node to delete, from list_nodes.")


LIST_COLUMNS = "id, parent_id, kind, title, description, icon, color, position, on_home"
CHILD_COLUMNS = "id, kind, title, icon, color, description, position"


def _next_position(client, parent_id: int | None) -> int:
    query = (
        client.table("nodes").select("position").order("position", desc=True).limit(1)
    )
    if parent_id is None:
        query = query.is_("parent_id", "null")
    else:
        query = query.eq("parent_id", parent_id)
    rows = query.execute().data
    return rows[0]["position"] + 1 if rows else 0


def _tree(rows: list[dict]) -> list[dict]:
    nodes = {row["id"]: {**row, "children": []} for row in rows}
    roots: list[dict] = []
    for row in rows:
        node = nodes[row["id"]]
        parent_id = row["parent_id"]
        if parent_id is not None and parent_id in nodes:
            nodes[parent_id]["children"].append(node)
        else:
            roots.append(node)
    return roots


@action(
    name="list_nodes",
    read_only=True,
    tool=True,
    mcp=True,
    description="The class's content tree: every section and page with its id, title and description, nested. Start here to find a page's id or where something belongs. It has no page content: use view_node for that.",
    method="GET",
    path="/nodes",
)
def list_nodes(ctx: Context, params: None):
    rows = (
        ctx.client.table("nodes")
        .select(LIST_COLUMNS)
        .order("position")
        .execute()
        .data
    )
    return _tree(rows)


@action(
    name="view_node",
    read_only=True,
    tool=True,
    mcp=True,
    description="One section or page by id: its fields, its children and, for a page, its Markdown and files, plus its web (OpenUI Lang) with include_web. Use it to read a page before answering about it or changing it. For the whole tree, list_nodes.",
    params=ViewNodeParams,
    method="GET",
    path="/node",
)
def view_node(ctx: Context, params: ViewNodeParams):
    # The content comes in the same read; a section has none to show, so it is dropped.
    rows = (
        ctx.client.table("nodes")
        .select(f"{LIST_COLUMNS}, content_md, content_web")
        .eq("id", params.node_id)
        .limit(1)
        .execute()
        .data
    )
    if not rows:
        raise HTTPException(404, f"There is no node {params.node_id}; list_nodes shows the tree")
    node = rows[0]

    if node["kind"] != "page":
        node.pop("content_md", None)
        node.pop("content_web", None)
    else:
        node["files"] = node_files(ctx.client, params.node_id)

    node["children"] = (
        ctx.client.table("nodes")
        .select(CHILD_COLUMNS)
        .eq("parent_id", params.node_id)
        .order("position")
        .execute()
        .data
    )
    return node


@action(
    name="create_node",
    tool=True,
    mcp=True,
    description="Add a section (it groups other nodes) or a page (it holds content) at the end of its parent's children. Admin only. A page starts empty: its content comes from the notes, not from here. To place it elsewhere, follow with move_node.",
    params=CreateNodeParams,
    path="/node",
    min_role="admin",
)
def create_node(ctx: Context, params: CreateNodeParams):
    row = params.model_dump(exclude_unset=True)
    row["position"] = _next_position(ctx.client, params.parent_id)
    return ctx.client.table("nodes").insert(row).execute().data[0]


@action(
    name="update_node",
    tool=True,
    mcp=True,
    description="Change a node's title, description, icon, colour or whether it is on the home screen. Only the fields given change. Admin only. It doesn't change a page's content, nor where it sits: that is move_node.",
    params=UpdateNodeParams,
    path="/node/update",
    min_role="admin",
)
def update_node(ctx: Context, params: UpdateNodeParams):
    data = params.model_dump(exclude_unset=True)
    data.pop("node_id", None)

    if not data:
        rows = (
            ctx.client.table("nodes")
            .select("*")
            .eq("id", params.node_id)
            .limit(1)
            .execute()
            .data
        )
        if not rows:
            raise HTTPException(404, f"There is no node {params.node_id}; list_nodes shows the tree")
        return rows[0]

    rows = (
        ctx.client.table("nodes")
        .update(data)
        .eq("id", params.node_id)
        .execute()
        .data
    )
    if not rows:
        raise HTTPException(404, f"There is no node {params.node_id}; list_nodes shows the tree")
    return rows[0]


@action(
    name="move_node",
    tool=True,
    mcp=True,
    description="Move a node under another parent, or to another place among its siblings: first, right after one of them, or last. Admin only. Everything under it moves with it.",
    params=MoveNodeParams,
    path="/node/move",
    min_role="admin",
)
def move_node(ctx: Context, params: MoveNodeParams):
    nodes = ctx.client.table("nodes").select("id, parent_id, position").execute().data
    by_id = {n["id"]: n for n in nodes}
    if params.node_id not in by_id:
        raise HTTPException(404, f"There is no node {params.node_id}; list_nodes shows the tree")
    # Left out, the parent is the one it has: a model asking for "last" means among its siblings,
    # not at the top level. The web always sends it.
    parent_id = params.parent_id if "parent_id" in params.model_fields_set else by_id[params.node_id]["parent_id"]
    if parent_id is not None and parent_id not in by_id:
        raise HTTPException(404, f"There is no node {parent_id}; list_nodes shows the tree")

    # Walking up from the new parent must not reach the node: it would end up inside itself.
    cursor = parent_id
    while cursor is not None:
        if cursor == params.node_id:
            raise HTTPException(422, "A node can't go inside itself or one of its own children")
        cursor = by_id[cursor]["parent_id"]

    if params.placement is None:
        data = {"parent_id": parent_id}
    else:
        siblings = [
            n for n in nodes
            if n["parent_id"] == parent_id and n["id"] != params.node_id
        ]
        if params.placement == "after" and params.after_node_id not in {s["id"] for s in siblings}:
            raise HTTPException(
                422,
                f"Node {params.after_node_id} is not under that parent; list_nodes shows the tree",
            )
        slot, moves = place_among(siblings, params.placement, params.after_node_id)
        for sibling_id, position in moves.items():
            ctx.client.table("nodes").update({"position": position}).eq("id", sibling_id).execute()
        data = {"parent_id": parent_id, "position": slot}

    rows = ctx.client.table("nodes").update(data).eq("id", params.node_id).execute().data
    if not rows:
        raise HTTPException(404, f"There is no node {params.node_id}; list_nodes shows the tree")
    return rows[0]


@action(
    name="reorder_nodes",
    description="Set the position of each node to its index in the list.",
    params=ReorderNodesParams,
    path="/node/reorder",
    min_role="admin",
)
def reorder_nodes(ctx: Context, params: ReorderNodesParams):
    for index, node_id in enumerate(params.ids):
        ctx.client.table("nodes").update({"position": index}).eq(
            "id", node_id
        ).execute()
    return {"ok": True}


@action(
    name="delete_node",
    tool=True,
    mcp=True,
    description="Delete a node and everything under it: its sections and pages, their content and their files. Admin only, confirmed, and it can't be undone. To only get it out of the way, move it.",
    params=NodeIdParams,
    path="/node/delete",
    requires_confirmation=True,
    min_role="admin",
)
def delete_node(ctx: Context, params: NodeIdParams):
    rows = ctx.client.table("nodes").delete().eq("id", params.node_id).execute().data
    if not rows:
        raise HTTPException(404, f"There is no node {params.node_id}; list_nodes shows the tree")
    return {"ok": True}
