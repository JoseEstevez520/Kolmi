import logging
import threading

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


class ListPassesParams(BaseModel):
    limit: int = 20


log = logging.getLogger(__name__)


def _run_in_background() -> None:
    try:
        run_daily_pass()
    except Exception:  # the pass records its own failure in ai_passes
        log.exception("the pass started from the admin failed")


@action(
    name="run_pass",
    tool=True,
    mcp=True,
    description="Start the AI pass now, in the background, instead of waiting for its schedule.",
    path="/pass/run",
    requires_confirmation=True,
    min_role="admin",
)
def run_pass(ctx: Context, params: None):
    from ..passes.daily import STALE_MINUTES
    from ..store import SupabaseStore

    # It returns at once; the pass shows up in the log. The pass itself refuses to start
    # while another is fresh, so the check here is only to answer straight away.
    if SupabaseStore(ctx.client).running_pass(STALE_MINUTES):
        return {"status": "already_running"}
    threading.Thread(target=_run_in_background, daemon=True).start()
    return {"status": "started"}


@action(
    name="list_passes",
    read_only=True,
    tool=True,
    mcp=True,
    description="The recent AI passes, with their status and stats, newest first.",
    params=ListPassesParams,
    method="GET",
    path="/passes",
    min_role="admin",
)
def list_passes(ctx: Context, params: ListPassesParams | None):
    limit = params.limit if params else 20
    return (
        ctx.client.table("ai_passes")
        .select("*")
        .order("started_at", desc=True)
        .limit(limit)
        .execute()
        .data
    )


@action(
    name="view_ai_log",
    read_only=True,
    tool=True,
    mcp=True,
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
    read_only=True,
    tool=True,
    mcp=True,
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
