from fastapi import HTTPException
from pydantic import BaseModel, Field

from ..auth import Context
from .registry import action


class EventIdParams(BaseModel):
    event_id: int = Field(..., description="The slot's id, from list_schedule_events.")


class CreateEventParams(BaseModel):
    node_id: int | None = Field(None, description="The page or section the slot is for, from list_nodes; null for none. Without a title or colour of its own, the slot takes the node's.")
    day: int = Field(..., description="The day, an index into get_settings's schedule_days, 0 the first.")
    start_time: str = Field(..., description="When it starts, HH:MM.")
    end_time: str = Field(..., description="When it ends, HH:MM.")
    title: str | None = Field(None, description="The slot's title; null to take the linked node's.")
    detail: str | None = Field(None, description="A line of detail, such as a room or a topic.")
    color: str | None = Field(None, description="Its colour as for a node; null to take the linked node's.")


class UpdateEventParams(BaseModel):
    event_id: int = Field(..., description="The slot to change, from list_schedule_events.")
    node_id: int | None = Field(None, description="The page or section the slot is for, from list_nodes.")
    day: int | None = Field(None, description="The day, an index into get_settings's schedule_days, 0 the first.")
    start_time: str | None = Field(None, description="When it starts, HH:MM.")
    end_time: str | None = Field(None, description="When it ends, HH:MM.")
    title: str | None = Field(None, description="The slot's title.")
    detail: str | None = Field(None, description="A line of detail, such as a room or a topic.")
    color: str | None = Field(None, description="Its colour as for a node.")


# A slot with no title or colour of its own takes its linked node's, so a slot that just
# points at a page never goes stale when the page is renamed or recoloured.
def _resolve(event: dict, nodes_by_id: dict[int, dict]) -> dict:
    node = nodes_by_id.get(event.get("node_id"))
    out = dict(event)
    if node:
        out["title"] = event.get("title") or node.get("title")
        out["color"] = event.get("color") or node.get("color")
        out["to"] = f"/node/{node['id']}"
    return out


@action(
    name="list_schedule_events",
    read_only=True,
    tool=True,
    mcp=True,
    description="The class's weekly timetable: each slot's day, hours, title, detail and linked page. day is an index into get_settings's schedule_days, 0 the first.",
    method="GET",
    path="/schedule/events",
)
def list_schedule_events(ctx: Context, params: None):
    events = ctx.client.table("schedule_events").select("*").order("day").execute().data
    node_ids = {e["node_id"] for e in events if e.get("node_id") is not None}
    nodes = (
        ctx.client.table("nodes").select("id, title, color").in_("id", list(node_ids)).execute().data
        if node_ids
        else []
    )
    nodes_by_id = {n["id"]: n for n in nodes}
    return [_resolve(e, nodes_by_id) for e in events]


@action(
    name="create_schedule_event",
    tool=True,
    description="Add a slot to the class's weekly timetable: a day, start and end hours, and optionally a title, a detail and the page it is for. Admin only. day is an index into get_settings's schedule_days, 0 the first.",
    params=CreateEventParams,
    path="/schedule/events",
    min_role="admin",
)
def create_schedule_event(ctx: Context, params: CreateEventParams):
    row = params.model_dump(exclude_unset=True)
    return ctx.client.table("schedule_events").insert(row).execute().data[0]


@action(
    name="update_schedule_event",
    tool=True,
    description="Change a timetable slot's day, hours, title, detail, colour or linked page. Only the fields given change. Admin only. Find the slot's id with list_schedule_events.",
    params=UpdateEventParams,
    path="/schedule/events/update",
    min_role="admin",
)
def update_schedule_event(ctx: Context, params: UpdateEventParams):
    data = params.model_dump(exclude_unset=True)
    data.pop("event_id", None)
    rows = (
        ctx.client.table("schedule_events")
        .update(data)
        .eq("id", params.event_id)
        .execute()
        .data
    )
    if not rows:
        raise HTTPException(404, f"There is no slot {params.event_id}; list_schedule_events lists them")
    return rows[0]


@action(
    name="delete_schedule_event",
    tool=True,
    requires_confirmation=True,
    description="Remove a slot from the class's weekly timetable. Admin only, confirmed, and it can't be undone. Find the slot's id with list_schedule_events.",
    params=EventIdParams,
    path="/schedule/events/delete",
    min_role="admin",
)
def delete_schedule_event(ctx: Context, params: EventIdParams):
    rows = (
        ctx.client.table("schedule_events").delete().eq("id", params.event_id).execute().data
    )
    if not rows:
        raise HTTPException(404, f"There is no slot {params.event_id}; list_schedule_events lists them")
    return {"ok": True}
