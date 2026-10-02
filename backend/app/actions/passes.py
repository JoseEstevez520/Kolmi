from pydantic import BaseModel

from ..auth import Context
from ..passes import run_daily_pass
from .registry import action


class ViewAiLogParams(BaseModel):
    pass_id: int | None = None
    since: str | None = None
    limit: int = 100


class ListNotesParams(BaseModel):
    status: str | None = None
    node_id: int | None = None


@action(
    name="run_pass",
    description="Run the AI pass now instead of waiting for the night.",
    path="/pass/run",
    requires_confirmation=True,
    min_role="admin",
)
def run_pass(ctx: Context, params: None):
    return run_daily_pass()


@action(
    name="view_ai_log",
    description="What the AI did: which notes it processed, which pages it changed or flagged.",
    params=ViewAiLogParams,
    method="GET",
    path="/ai-log",
    min_role="admin",
)
def view_ai_log(ctx: Context, params: ViewAiLogParams | None):
    query = ctx.client.table("ai_log").select("*")
    if params and params.pass_id is not None:
        query = query.eq("pass_id", params.pass_id)
    if params and params.since:
        query = query.gte("created_at", params.since)
    limit = params.limit if params else 100
    return query.order("created_at", desc=True).limit(limit).execute().data


@action(
    name="list_notes",
    description="List the notes students have left, with their status.",
    params=ListNotesParams,
    method="GET",
    path="/notes",
    min_role="admin",
)
def list_notes(ctx: Context, params: ListNotesParams | None):
    query = ctx.client.table("notes").select(
        "id, content, status, created_at, node_id, user_id, profiles(name)"
    )
    if params and params.status:
        query = query.eq("status", params.status)
    if params and params.node_id is not None:
        query = query.eq("node_id", params.node_id)
    return query.order("created_at", desc=True).execute().data
