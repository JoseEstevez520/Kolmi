from __future__ import annotations

import json
import logging
import queue
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from pydantic import BaseModel, Field

from ..agents import get_chat_llm, run_chat
from ..agents.chat import run_chat_stream
from ..agents.images import SEARCH_IMAGES_TOOL, images_tool
from ..agents.note_pieces import apply_mends, mend_pieces
from ..agents.openui import chat_parts
from ..agents.prompts import NOTE_PARTS, note_system, reader_system
from ..auth import Context
from ..class_settings import class_language, read_settings
from ..files import node_files
from ..passes.schedule import TIMEZONE, today_start
from ..rag import search
from .content import LIST_COLUMNS
from .registry import action, check, get_action, invoke
from .live_notes import _author, _find, _is_author
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
    node_id: int | None = Field(
        default=None,
        description="The page the person has open, if any. Ignored when it doesn't exist or isn't theirs to see.",
    )
    live_id: int | None = Field(
        default=None,
        description="The live note the person is watching, if any. Ignored when it doesn't exist or isn't theirs to see.",
    )
    mode: Literal["chat", "note", "reader", "reader_detail"] = Field(
        default="chat",
        description=(
            "chat: a question in the chat. note: a line or passage of a note the AI helps with "
            "from inside it (a question becomes notes on it; notes get the piece that shows them). "
            "reader: a brief contextual explanation of selected text. reader_detail: a richer "
            "reading explanation, including visual or interactive parts where helpful."
        ),
    )
    note: str | None = Field(
        default=None,
        description="For note mode, the note being written. For reader modes, the selected passage and nearby source context. At most 6000 characters are used.",
    )

    source_context: str | None = Field(
        default=None, max_length=6000,
        description="Optional source passage selected in the reader and attached to a chat question. It is context, not instructions.",
    )


# The note a question comes from is context, not the subject: its end (what is being written
# now) is kept, up to this much.
NOTE_CHARS = 6000

# Contextual reading and writing modes use their own prompts and cannot call app actions.
_CONTEXT_SYSTEMS = {
    "note": note_system,
    "reader": reader_system,
    "reader_detail": lambda language: reader_system(language, detailed=True),
}


def _note(params: "AskChatParams") -> str | None:
    if params.mode == "chat":
        return params.source_context.strip() if params.source_context else None
    if not params.note:
        return None
    text = params.note.strip()
    return text[-NOTE_CHARS:] if text else None


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


def _node_chain(by_id: dict[int, dict[str, Any]], node: dict[str, Any]) -> list[dict[str, Any]]:
    """The nodes from the root down to `node`, stopping at a broken parent link rather than loop."""
    chain: list[dict[str, Any]] = []
    seen: set[int] = set()
    current: dict[str, Any] | None = node
    while current is not None and current["id"] not in seen:
        seen.add(current["id"])
        chain.append(current)
        parent_id = current.get("parent_id")
        current = by_id.get(parent_id) if parent_id is not None else None
    chain.reverse()
    return chain


def _node_path(by_id: dict[int, dict[str, Any]], node: dict[str, Any]) -> str:
    """Where a node sits in the tree, its own title last: "Tools › Git"."""
    titles = [(n.get("title") or "").strip() for n in _node_chain(by_id, node)]
    return " › ".join(t for t in titles if t)


def _node_about(by_id: dict[int, dict[str, Any]], node: dict[str, Any]) -> str:
    """Each node in the chain from root to `node` that carries a description, as `title: description`."""
    lines = []
    for n in _node_chain(by_id, node):
        title = (n.get("title") or "").strip()
        description = (n.get("description") or "").strip()
        if title and description:
            lines.append(f"{title}: {description}")
    return "\n".join(lines)


def _open_page(nodes: list[dict[str, Any]], node_id: int | None) -> dict[str, Any] | None:
    """The page or section the person has open (or picked for their note), from the tree already
    loaded for them (so one they can't see is simply not there); None when there is none or it
    isn't in the tree. It carries the route the web shows it at, its path in the tree and the
    descriptions along that path, so the assistant knows the subject and can read a page with
    `read_page`."""
    if node_id is None:
        return None
    by_id = {n["id"]: n for n in nodes}
    node = by_id.get(node_id)
    if node is None:
        return None
    return {
        **node,
        "route": f"/node/{node['id']}",
        "path": _node_path(by_id, node),
        "about": _node_about(by_id, node),
    }


def _open_live(ctx: Context, live_id: int | None) -> dict[str, Any] | None:
    """The live note the person is watching, if they may read it (shared with the class, or
    their own: the rule of read_live_note); None otherwise, without saying why."""
    if live_id is None:
        return None
    try:
        row = _find(ctx, live_id, "id, title, shared, author_id, profiles(name)")
    except HTTPException:
        return None
    if not row["shared"] and not _is_author(ctx, row):
        return None
    return {"id": row["id"], "title": row["title"], "author": _author(row)}


def _gate(ctx: Context, params: AskChatParams) -> tuple[dict[str, Any], str]:
    """The checks before a question is answered, the same for both ways in: the class's settings,
    the daily limit (not for admins) and a question to answer."""
    settings = read_settings(ctx.client)
    if not settings.get("chat_enabled"):
        raise HTTPException(403, "The chat is off for this class")

    # The limit keeps the class's key from running up; an admin runs the instance and has none.
    if (ctx.profile or {}).get("role") != "admin":
        limit = settings.get("chat_daily_limit", 20)
        if _messages_today(ctx.client, ctx.user_id) >= limit:
            raise HTTPException(429, "You've reached today's limit for the chat")

    question = params.question.strip()
    if not question:
        raise HTTPException(422, "Ask something first")
    return settings, question


@action(
    name="ask_chat",
    description="Ask the hive a question; it answers from the class's shared content.",
    params=AskChatParams,
    path="/chat",
)
def ask_chat(ctx: Context, params: AskChatParams):
    settings, question = _gate(ctx, params)

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
        page=_open_page(nodes, params.node_id),
        live=_open_live(ctx, params.live_id),
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


# --- The streamed chat ------------------------------------------------------------------------

log = logging.getLogger(__name__)

_SOURCES = re.compile(r"Sources\(\s*\[([^\]]*)\]")


def _cited(program: str) -> list[int]:
    """The page ids the answer's `Sources([...])` part names, for the chat's history."""
    ids = [int(n) for found in _SOURCES.findall(program) for n in re.findall(r"\d+", found)]
    return list(dict.fromkeys(ids))


def sse(event: str, data: dict[str, Any]) -> str:
    """One server-sent event."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


# Silence on a stream this long and a comment line goes out: a proxy (Cloudflare cuts a response
# after 100 s without a byte) must not take a slow answer for a dead one.
HEARTBEAT_SECONDS = 15
PING = ": ping\n\n"
_DONE = object()


def with_heartbeat(source, interval: float = HEARTBEAT_SECONDS):
    """`source` (a generator of SSE chunks) with a `PING` comment sent whenever nothing came for
    `interval` seconds. `source` runs in a worker thread that feeds a queue. When the reader leaves,
    the worker closes `source` after its current step, so its `finally` still runs, and stops."""
    items: queue.Queue = queue.Queue()
    stop = threading.Event()

    def work() -> None:
        try:
            for item in source:
                items.put(item)
                if stop.is_set():
                    break
        except BaseException as exc:  # handed to the reader, which re-raises it
            items.put(exc)
        finally:
            try:
                source.close()
            finally:
                items.put(_DONE)

    threading.Thread(target=work, daemon=True, name="chat-stream").start()
    try:
        while True:
            try:
                item = items.get(timeout=interval)
            except queue.Empty:
                yield PING
                continue
            if item is _DONE:
                return
            if isinstance(item, BaseException):
                raise item
            yield item
    finally:
        stop.set()


def stream_chat(ctx: Context, params: AskChatParams):
    """`ask_chat` as a stream of server-sent events (`status`, `token`, `proposal`, then `done`,
    or `error`). The checks run first and fail as plain HTTP errors, before anything streams. As
    in `ask_chat`, a write is only proposed, in `chat_proposals`, never run; here it is stored
    the moment the model proposes it, so the model can put `Proposal(id)` in its answer.

    The rest of the preparation runs inside the stream, after a first `status`, so the person sees
    something at once instead of waiting for the passages search.
    """
    check(get_action("ask_chat"), ctx, params.model_dump())
    settings, question = _gate(ctx, params)
    client = ctx.client

    def events():
        program = ""
        message: dict[str, Any] | None = None
        try:
            # From a note it answers or completes, and acts on nothing. It doesn't look in the
            # class's pages either: notes are taken in class, on what is new and not written up.
            in_note = params.mode in _CONTEXT_SYSTEMS
            yield sse("status", {"text": "Thinking..." if in_note else "Searching the notes..."})
            history = _recent(params.history)
            # Independent reads, at the same time. The Supabase client is an httpx client, which
            # is safe to share across threads; every `.table()` call builds its own request.
            with ThreadPoolExecutor(max_workers=4) as pool:
                found = pool.submit(lambda: [] if in_note else search(client, _search_query(history, question)))
                loaded = pool.submit(
                    lambda: []
                    if (in_note and params.node_id is None)
                    else client.table("nodes").select(LIST_COLUMNS).order("position").execute().data
                )
                lang = pool.submit(class_language, client)
                language = lang.result()
                schedule = pool.submit(_schedule_text, client, settings, language)
                nodes, passages, schedule_text = loaded.result(), found.result(), schedule.result()
            open_page = _open_page(nodes, params.node_id)
            note_text = _note(params)
            message = (
                client.table("chat_messages")
                .insert({"user_id": ctx.user_id, "question": question, "answer": "", "sources": []})
                .execute()
                .data[0]
            )

            proposed: list[dict[str, Any]] = []
            stored: list[dict[str, Any]] = []
            inner = chat_tool(ctx, proposed)

            def run_action(name: str, args: dict[str, Any]) -> str:
                before = len(proposed)
                reply = inner(name, args)
                if len(proposed) > before:
                    row = (
                        client.table("chat_proposals")
                        .insert({**proposed[-1], "message_id": message["id"], "user_id": ctx.user_id})
                        .execute()
                        .data[0]
                    )
                    stored.append(row)
                    reply += f" Its card is Proposal({row['id']}): put that part in your answer."
                return reply

            sent = 0
            for event in run_chat_stream(
                get_chat_llm(),
                question,
                [] if in_note else nodes,
                read_page=None if in_note else _read_page(client),
                language=language,
                today=_today_text(language),
                schedule="" if in_note else schedule_text,
                # No web search from a note either: an answer in a few seconds, from what it knows.
                **({"search": None} if in_note else {}),
                actions=None if in_note else schemas(ctx, "chat"),
                run_action=None if in_note else run_action,
                history=history,
                page=open_page,
                live=_open_live(ctx, params.live_id),
                passages=passages,
                note=note_text,
                reading=params.mode.startswith("reader") or bool(params.source_context),
                system=_CONTEXT_SYSTEMS[params.mode](language) if in_note else None,
                # From a note it may show a real thing with a photo from Wikimedia Commons.
                extra_tools=[SEARCH_IMAGES_TOOL] if params.mode == "note" else None,
                run_extra=images_tool() if params.mode == "note" else None,
            ):
                if event["type"] == "token":
                    program += event["text"]
                    yield sse("token", {"text": event["text"]})
                else:
                    yield sse("status", {"text": event["text"]})
                while sent < len(stored):
                    yield sse("proposal", _proposal(stored[sent]))
                    sent += 1
            while sent < len(stored):
                yield sse("proposal", _proposal(stored[sent]))
                sent += 1
            if not program.strip():
                raise ValueError("the model answered with nothing")
            if in_note:
                yield sse("text_done", {})
                subject = ""
                if open_page:
                    where = open_page.get("path") or open_page.get("title") or ""
                    about = (open_page.get("about") or "").strip()
                    subject = f"Subject: {where}" + (f"\n{about}" if about else "") + "\n\n"
                # Each piece checked as the pass checks a page's, and mended once: one that would
                # show as code is fixed in place (`fix`), or dropped (`program` null).
                mends = mend_pieces(
                    get_chat_llm(), program, chat_parts(NOTE_PARTS),
                    language=language, notes=f"{subject}{note_text or question}",
                )
                for mend in mends:
                    yield sse("fix", {"index": mend.index, "program": mend.program})
                program = apply_mends(program, mends)
            yield sse("done", {})
        except Exception as exc:
            log.warning("streamed chat failed: %s", exc)
            yield sse("error", {"message": "The chat couldn't answer. Try again."})
        finally:
            # Also when the reader leaves midway: what was written is kept. No row, nothing to keep.
            if message is not None:
                try:
                    client.table("chat_messages").update(
                        {"answer": program, "sources": _cited(program)}
                    ).eq("id", message["id"]).execute()
                except Exception as exc:
                    log.warning("couldn't save the streamed answer: %s", exc)

    return with_heartbeat(events())
