from fastapi import HTTPException
from pydantic import BaseModel

from ..auth import Context
from .registry import action


class EventIdParams(BaseModel):
    event_id: int


class CreateEventParams(BaseModel):
    node_id: int | None = None
    day: int
    start_time: str
    end_time: str
    title: str | None = None
    detail: str | None = None
    color: str | None = None


class UpdateEventParams(BaseModel):
    event_id: int
    node_id: int | None = None
    day: int | None = None
    start_time: str | None = None
    end_time: str | None = None
    title: str | None = None
    detail: str | None = None
    color: str | None = None


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
    description="The class timetable's slots, each with its day, hours and what it's for.",
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
    description="Add a slot to the class timetable.",
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
    description="Change a timetable slot's day, hours, title, colour or linked page.",
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
        raise HTTPException(404, "Slot not found")
    return rows[0]


@action(
    name="delete_schedule_event",
    tool=True,
    requires_confirmation=True,
    description="Remove a slot from the class timetable.",
    params=EventIdParams,
    path="/schedule/events/delete",
    min_role="admin",
)
def delete_schedule_event(ctx: Context, params: EventIdParams):
    rows = (
        ctx.client.table("schedule_events").delete().eq("id", params.event_id).execute().data
    )
    if not rows:
        raise HTTPException(404, "Slot not found")
    return {"ok": True}
