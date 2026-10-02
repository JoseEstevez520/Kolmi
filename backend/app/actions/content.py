from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel

from ..auth import Context
from .registry import action


class ViewNodeParams(BaseModel):
    node_id: int


class CreateNodeParams(BaseModel):
    parent_id: int | None = None
    kind: Literal["section", "page"]
    title: str
    description: str | None = None
    icon: str | None = None
    color: str | None = None
    on_home: bool | None = None


class UpdateNodeParams(BaseModel):
    node_id: int
    title: str | None = None
    description: str | None = None
    icon: str | None = None
    color: str | None = None
    on_home: bool | None = None
    content_md: str | None = None
    content_web: str | None = None


class MoveNodeParams(BaseModel):
    node_id: int
    parent_id: int | None = None


class ReorderNodesParams(BaseModel):
    ids: list[int]


class NodeIdParams(BaseModel):
    node_id: int


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
    description="List the whole content tree, nodes nested with their children.",
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
    description="Get a node with its children and, for pages, its content.",
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
        raise HTTPException(404, "Node not found")
    node = rows[0]

    if node["kind"] != "page":
        node.pop("content_md", None)
        node.pop("content_web", None)

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
    description="Create a node at the end of its siblings.",
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
    description="Update the fields of a node that are given.",
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
            raise HTTPException(404, "Node not found")
        return rows[0]

    rows = (
        ctx.client.table("nodes")
        .update(data)
        .eq("id", params.node_id)
        .execute()
        .data
    )
    if not rows:
        raise HTTPException(404, "Node not found")
    return rows[0]


@action(
    name="move_node",
    description="Change the parent of a node.",
    params=MoveNodeParams,
    path="/node/move",
    min_role="admin",
)
def move_node(ctx: Context, params: MoveNodeParams):
    rows = (
        ctx.client.table("nodes")
        .update({"parent_id": params.parent_id})
        .eq("id", params.node_id)
        .execute()
        .data
    )
    if not rows:
        raise HTTPException(404, "Node not found")
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
    description="Delete a node and everything under it.",
    params=NodeIdParams,
    path="/node/delete",
    requires_confirmation=True,
    min_role="admin",
)
def delete_node(ctx: Context, params: NodeIdParams):
    rows = ctx.client.table("nodes").delete().eq("id", params.node_id).execute().data
    if not rows:
        raise HTTPException(404, "Node not found")
    return {"ok": True}
