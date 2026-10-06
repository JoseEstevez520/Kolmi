from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from pydantic import BaseModel, Field

from ..agents import get_chat_llm, run_chat
from ..auth import Context
from ..class_settings import class_language, read_settings
from ..files import node_files
from ..passes.schedule import TIMEZONE, today_start
from ..rag import search
from .content import LIST_COLUMNS
from .registry import action, check, get_action, invoke
from .schedule import _resolve
from .tools import answer as tool_answer
from .tools import chat_tool, offered, schemas

_DAY_NAMES = {
    "es": {1: "Lunes", 2: "Martes", 3: "Miércoles", 4: "Jueves", 5: "Viernes", 6: "Sábado", 7: "Domingo"},
    "en": {1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 5: "Friday", 6: "Saturday", 7: "Sunday"},
}


def _today_text(language: str, tz: str = TIMEZONE) -> str:
    """Today's weekday and date in the class's timezone, as one line: the model otherwise has no
    notion of "today", so it can't work out what "tomorrow" or "this weekend" means on its own.
    """
    now = datetime.now(ZoneInfo(tz))
    names = _DAY_NAMES.get(language, _DAY_NAMES["en"])
    day = names.get(now.isoweekday(), str(now.isoweekday()))
    return f"{day}, {now.date().isoformat()}"


def _schedule_text(client, settings: dict, language: str) -> str:
    """The class timetable as plain text for the chat's context: each slot's day, hours and
    what it's for, in the same shape list_schedule_events shows an admin. Empty when the class
    hasn't turned the timetable on.
    """
    if not settings.get("schedule_enabled"):
        return ""
    events = client.table("schedule_events").select("*").order("day").execute().data
    if not events:
        return ""
    node_ids = {e["node_id"] for e in events if e.get("node_id") is not None}
    nodes = (
        client.table("nodes").select("id, title, color").in_("id", list(node_ids)).execute().data
        if node_ids
        else []
    )
    nodes_by_id = {n["id"]: n for n in nodes}
    names = _DAY_NAMES.get(language, _DAY_NAMES["en"])
    # `event.day` indexes into the admin's chosen days (ISO weekdays, Monday first), not a
    # weekday number itself: the same shape elastic-ui's Timetable and ScheduleView use.
    week_days = settings.get("schedule_days") or []
    lines = []
    for event in sorted(events, key=lambda e: (e["day"], e["start_time"])):
        resolved = _resolve(event, nodes_by_id)
        iso_day = week_days[resolved["day"]] if 0 <= resolved["day"] < len(week_days) else None
        day = names.get(iso_day, str(resolved["day"]))
        detail = f" ({resolved['detail']})" if resolved.get("detail") else ""
        lines.append(f"- {day} {resolved['start_time']}-{resolved['end_time']}: {resolved['title']}{detail}")
    return "\n".join(lines)


# What the chat remembers of the conversation so far: the last few turns, as the web sent them.
# The browser isn't trusted, so the count and each text are capped here too.
HISTORY_TURNS = 6
HISTORY_CHARS = 1500


def _search_query(history: list[dict[str, str]], question: str) -> str:
    asked = [m["text"] for m in history if m["role"] == "user"][-1:]
    return " ".join([*asked, question])


class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    text: str


class AskChatParams(BaseModel):
    question: str
    history: list[HistoryMessage] = Field(
        default_factory=list,
        max_length=40,
        description="The conversation so far, oldest first: only the last turns are used.",
    )


def _recent(history: list[HistoryMessage]) -> list[dict[str, str]]:
    turns = [{"role": m.role, "text": m.text.strip()[:HISTORY_CHARS]} for m in history if m.text.strip()]
    return turns[-HISTORY_TURNS:]


def _proposal(row: dict[str, Any]) -> dict[str, Any]:
    """A proposal as the web shows it: whether it destroys something comes from its action."""
    found = get_action(row["tool"])
    return {
        "id": row["id"],
        "tool": row["tool"],
        "args": row.get("args") or {},
        "status": row["status"],
        "destructive": bool(found and found.requires_confirmation),
        "result": row.get("result"),
    }


def _messages_today(client, user_id: str) -> int:
    rows = (
        client.table("chat_messages")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .gte("created_at", today_start())
        .execute()
    )
    return rows.count or 0


def _read_page(client):
    def read(node_id: int) -> dict[str, Any] | None:
        rows = (
            client.table("nodes")
            .select("id, content_md")
            .eq("id", node_id)
            .limit(1)
            .execute()
            .data
        )
        if not rows:
            return None
        return {**rows[0], "files": node_files(client, node_id)}

    return read


@action(
    name="ask_chat",
    description="Ask the hive a question; it answers from the class's shared content.",
    params=AskChatParams,
    path="/chat",
)
def ask_chat(ctx: Context, params: AskChatParams):
    settings = read_settings(ctx.client)
    if not settings.get("chat_enabled"):
        raise HTTPException(403, "The chat is off for this class")

    limit = settings.get("chat_daily_limit", 20)
    if _messages_today(ctx.client, ctx.user_id) >= limit:
        raise HTTPException(429, "You've reached today's limit for the chat")

    question = params.question.strip()
    if not question:
        raise HTTPException(422, "Ask something first")

    nodes = ctx.client.table("nodes").select(LIST_COLUMNS).order("position").execute().data
    language = class_language(ctx.client)
    history = _recent(params.history)
    # The asker's own tools, with their role: reads run in the loop, writes are only proposed.
    proposed: list[dict[str, Any]] = []
    answer = run_chat(
        get_chat_llm(),
        question,
        nodes,
        read_page=_read_page(ctx.client),
        language=language,
        today=_today_text(language),
        schedule=_schedule_text(ctx.client, settings, language),
        actions=schemas(ctx, "chat"),
        run_action=chat_tool(ctx, proposed),
        history=history,
        # The parts of the pages closest to the question; none with the search index off. A
        # follow-up ("and how is that set up?") says little alone, so it is searched with what
        # the person asked just before.
        passages=search(ctx.client, _search_query(history, question)),
    )
    if answer.from_index:
        # The loop failed: what it proposed on the way goes with it.
        proposed = []

    message = (
        ctx.client.table("chat_messages")
        .insert(
            {
                "user_id": ctx.user_id,
                "question": question,
                "answer": answer.answer,
                "sources": answer.sources,
            }
        )
        .execute()
        .data[0]
    )
    rows = (
        ctx.client.table("chat_proposals")
        .insert([{**p, "message_id": message["id"], "user_id": ctx.user_id} for p in proposed])
        .execute()
        .data
        if proposed
        else []
    )

    return {
        **answer.model_dump(),
        "message_id": message["id"],
        "proposals": [_proposal(row) for row in rows],
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _own_proposal(ctx: Context, proposal_id: int) -> dict[str, Any]:
    rows = (
        ctx.client.table("chat_proposals")
        .select("*")
        .eq("id", proposal_id)
        .eq("user_id", ctx.user_id)
        .limit(1)
        .execute()
        .data
    )
    if not rows:
        raise HTTPException(404, f"You have no chat proposal {proposal_id}")
    return rows[0]


def _set_proposal(
    ctx: Context, proposal_id: int, fields: dict[str, Any], *, pending: bool = False
) -> list[dict[str, Any]]:
    """Update one of the caller's proposals; with `pending`, only while it still is, so two
    clicks can't both claim it."""
    query = (
        ctx.client.table("chat_proposals")
        .update(fields)
        .eq("id", proposal_id)
        .eq("user_id", ctx.user_id)
    )
    if pending:
        query = query.eq("status", "pending")
    rows = query.execute().data
    if pending and not rows:
        raise HTTPException(409, "This proposal was already confirmed or cancelled")
    return rows


# A confirmation that never came back (a crash mid-run) must not leave a proposal stuck: past
# this long a `running` one counts as pending again.
STALE_RUNNING = timedelta(minutes=2)


def _release_stale(ctx: Context, row: dict[str, Any]) -> None:
    if row.get("status") != "running" or not row.get("decided_at"):
        return
    started = datetime.fromisoformat(str(row["decided_at"]).replace("Z", "+00:00"))
    if datetime.now(timezone.utc) - started < STALE_RUNNING:
        return
    (
        ctx.client.table("chat_proposals")
        .update({"status": "pending"})
        .eq("id", row["id"])
        .eq("user_id", ctx.user_id)
        .eq("status", "running")
        .execute()
    )


class ConfirmChatProposalParams(BaseModel):
    proposal_id: int
    args: dict[str, Any] | None = None


class CancelChatProposalParams(BaseModel):
    proposal_id: int


@action(
    name="confirm_chat_proposal",
    description=(
        "Run a change the chat proposed to you, as you and with your role. Without args it runs "
        "as proposed; with args, it runs with those instead (an edited proposal). A proposal runs "
        "once: one already confirmed or cancelled can't be."
    ),
    params=ConfirmChatProposalParams,
    path="/chat/confirm",
)
def confirm_chat_proposal(ctx: Context, params: ConfirmChatProposalParams):
    row = _own_proposal(ctx, params.proposal_id)
    ctx = replace(ctx, source="chat")
    # Checked before claiming it: a tool the caller has lost leaves the proposal as it was.
    found = next((a for a in offered(ctx, "chat") if a.name == row["tool"]), None)
    if found is None:
        raise HTTPException(403, f"You can't run {row['tool']} from the chat")
    args = params.args if params.args is not None else row.get("args") or {}
    # Validated before claiming it too, so a bad edit or a blocked asker never flips the proposal.
    try:
        checked = check(found, ctx, args)
    except HTTPException as exc:
        _set_proposal(ctx, params.proposal_id, {"result": f"Error {exc.status_code}: {exc.detail}"})
        raise
    args = checked.model_dump(mode="json", exclude_unset=True) if checked is not None else {}
    _release_stale(ctx, row)
    _set_proposal(ctx, params.proposal_id, {"status": "running", "decided_at": _now()}, pending=True)
    try:
        value = invoke(found, ctx, args)
    except HTTPException as exc:
        error = f"Error {exc.status_code}: {exc.detail}"
        _set_proposal(ctx, params.proposal_id, {"status": "pending", "result": error})
        raise
    except Exception:
        _set_proposal(ctx, params.proposal_id, {"status": "pending"})
        raise
    done = {"status": "done", "result": tool_answer(value), "decided_at": _now(), "args": args}
    rows = _set_proposal(ctx, params.proposal_id, done)
    return _proposal(rows[0] if rows else {**row, **done})


@action(
    name="cancel_chat_proposal",
    description=(
        "Cancel a change the chat proposed to you, so it never runs. Only a pending one can be."
    ),
    params=CancelChatProposalParams,
    path="/chat/cancel",
)
def cancel_chat_proposal(ctx: Context, params: CancelChatProposalParams):
    row = _own_proposal(ctx, params.proposal_id)
    cancelled = {"status": "cancelled", "decided_at": _now()}
    rows = _set_proposal(ctx, params.proposal_id, cancelled, pending=True)
    return _proposal(rows[0] if rows else {**row, **cancelled})
