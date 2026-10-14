import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from pydantic import BaseModel, Field

from ..auth import Context
from ..class_settings import read_settings
from ..passes.schedule import TIMEZONE
from .registry import action

# A shared, unended note counts as "being written now" while it was saved this recently. A writer
# who closes the tab without ending the session drops out of "Now" after this long.
LIVE_WINDOW = timedelta(minutes=5)
# A session ends by itself this long after it started: a class is not longer than this, and a
# writer who forgot to end it must not stay "live" all day.
MAX_SESSION = timedelta(hours=3)
# How much of the text the list shows, taken from the end: what was written last.
PREVIEW_CHARS = 140
MAX_CONTENT = 200_000
LIST_LIMIT = 60

# Who is following a session. The API is one process, so this lives in memory and needs no
# table: note id -> {user id: last time they read it, on the monotonic clock}. A restart
# empties it and the next poll refills it. A reader counts as following for FOLLOW_WINDOW after
# their last read (the web reads every 4 s), so a closed tab drops out within moments.
FOLLOW_WINDOW = 15.0
MAX_FOLLOWERS = 20
_seen: dict[int, dict[str, float]] = {}
_seen_lock = threading.Lock()

SUMMARY_COLUMNS = "id, author_id, note_id, title, event_id, shared, ended_at, created_at, updated_at, content, profiles(name)"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _stamp() -> str:
    return _now().isoformat()


def _parse(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def is_over(row: dict[str, Any], now: datetime | None = None) -> bool:
    """Ended by its author, or past MAX_SESSION since it started."""
    if row.get("ended_at"):
        return True
    started = _parse(row.get("created_at"))
    return started is not None and (now or _now()) - started >= MAX_SESSION


def is_live(row: dict[str, Any], now: datetime | None = None) -> bool:
    """Shared, not over, and saved within LIVE_WINDOW."""
    if not row.get("shared") or is_over(row, now):
        return False
    saved = _parse(row.get("updated_at"))
    return saved is not None and (now or _now()) - saved <= LIVE_WINDOW


def current_class(client) -> dict[str, Any] | None:
    """The timetable slot on right now, as {event_id, title}; None when the timetable is off,
    nothing is on or the slot has no title."""
    settings = read_settings(client)
    if not settings.get("schedule_enabled"):
        return None
    now = datetime.now(ZoneInfo(TIMEZONE))
    days = settings.get("schedule_days") or []
    if now.isoweekday() not in days:
        return None
    # `event.day` indexes into the admin's chosen days, not a weekday number.
    day = days.index(now.isoweekday())
    clock = now.strftime("%H:%M")
    events = client.table("schedule_events").select("*").eq("day", day).execute().data
    for event in sorted(events, key=lambda e: e["start_time"]):
        if event["start_time"] <= clock < event["end_time"]:
            title = event.get("title")
            if not title and event.get("node_id") is not None:
                nodes = client.table("nodes").select("title").eq("id", event["node_id"]).limit(1).execute().data
                title = nodes[0]["title"] if nodes else None
            return {"event_id": event["id"], "title": title}
    return None


def _author(row: dict[str, Any]) -> str | None:
    profile = row.get("profiles")
    if isinstance(profile, list):
        profile = profile[0] if profile else None
    return (profile or {}).get("name")


def _is_author(ctx: Context, row: dict[str, Any]) -> bool:
    return row.get("author_id") == ctx.user_id


def _shape(ctx: Context, row: dict[str, Any], now: datetime) -> dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "author": _author(row),
        "mine": _is_author(ctx, row),
        "shared": row["shared"],
        "live": is_live(row, now),
        "ended": is_over(row, now),
        "event_id": row.get("event_id"),
        # The note being mirrored: only its author needs it, so nobody else sees which one.
        "note_id": row.get("note_id") if _is_author(ctx, row) else None,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _find(ctx: Context, note_id: int, columns: str = "*, profiles(name)") -> dict[str, Any]:
    rows = ctx.client.table("live_notes").select(columns).eq("id", note_id).execute().data
    if not rows:
        raise HTTPException(404, f"There is no live note {note_id}; list_live_notes lists them")
    return rows[0]


def _own(ctx: Context, note_id: int) -> dict[str, Any]:
    """A note its author may write to; anyone else is told so."""
    row = _find(ctx, note_id)
    if not _is_author(ctx, row):
        raise HTTPException(403, "Only the author of a live note can change it; everyone else can read it")
    return row


class StartParams(BaseModel):
    title: str | None = Field(
        None,
        max_length=200,
        description="What the session is about, like 'Deployment class'. Left out, it takes the title of the class the timetable says is on now; if none is on, a title is required (a session linked to a note falls back to 'Untitled').",
    )
    note_id: int | None = Field(None, description="One of your own notes to mirror: the session is linked to it and the web pushes the note's text to it as you write. Left out, the session stands alone.")
    content: str | None = Field(None, max_length=MAX_CONTENT, description="The text to start with, as Markdown or plain text. Left out, the session starts empty.")
    shared: bool = Field(False, description="true opens the session to the class from the start; otherwise it starts private.")


def _end_open_sessions(ctx: Context) -> None:
    """A person writes live in one place at a time: whatever they had open ends now."""
    rows = ctx.client.table("live_notes").select("id, created_at, ended_at").eq("author_id", ctx.user_id).execute().data
    stamp = _stamp()
    for row in rows:
        if not is_over(row):
            ctx.client.table("live_notes").update({"ended_at": stamp, "updated_at": stamp}).eq("id", row["id"]).execute()


@action(
    name="start_live_note",
    description="Start a live note: a session where you write during a class and the rest of the class can watch the text appear. It starts private unless shared=true; save_live_note with shared=true opens it to the class. Pass note_id to mirror one of your own notes. You can write live in one place at a time: starting a session ends any other you had open. Linked to the class the timetable says is on now, if any.",
    params=StartParams,
    path="/live/start",
)
def start_live_note(ctx: Context, params: StartParams):
    if params.note_id is not None:
        owned = ctx.client.table("notes").select("id").eq("id", params.note_id).eq("user_id", ctx.user_id).execute().data
        if not owned:
            raise HTTPException(404, f"You have no note {params.note_id}; only your own notes can be shared live")
    on_now = current_class(ctx.client)
    title = (params.title or "").strip() or (on_now or {}).get("title") or ("Untitled" if params.note_id is not None else "")
    if not title:
        raise HTTPException(422, "Give the session a title: no class is on now to take it from")
    _end_open_sessions(ctx)
    now = _stamp()
    row = (
        ctx.client.table("live_notes")
        .insert(
            {
                "author_id": ctx.user_id,
                "note_id": params.note_id,
                "title": title,
                "event_id": (on_now or {}).get("event_id"),
                "content": params.content or "",
                "shared": params.shared,
                "created_at": now,
                "updated_at": now,
            }
        )
        .execute()
        .data[0]
    )
    return _shape(ctx, {**row, "profiles": {"name": (ctx.profile or {}).get("name")}}, _now())


class SaveParams(BaseModel):
    id: int = Field(..., description="The live note's id, from start_live_note or list_live_notes.")
    content: str | None = Field(None, max_length=MAX_CONTENT, description="The whole text of the note so far, as Markdown or plain text; it replaces what was saved. Left out, the text stays as it is.")
    shared: bool | None = Field(None, description="true opens the note to the class so they can watch it; false takes it back. Left out, it stays as it is.")
    title: str | None = Field(None, max_length=200, description="A new title. Left out, it stays.")


@action(
    name="save_live_note",
    description="Save a live note you are writing: its text (the whole text, replacing what was saved), whether it is shared with the class, or its title. Only the author can; the last save wins. An ended note can't be saved to, and a session ends by itself 3 hours after it started. Call it as the text changes so the class sees it.",
    params=SaveParams,
    path="/live/save",
)
def save_live_note(ctx: Context, params: SaveParams):
    row = _own(ctx, params.id)
    changes: dict[str, Any] = {}
    if params.content is not None:
        changes["content"] = params.content
    if params.shared is not None:
        changes["shared"] = params.shared
    if params.title is not None:
        if not params.title.strip():
            raise HTTPException(422, "The title can't be empty")
        changes["title"] = params.title.strip()
    if not changes:
        raise HTTPException(422, "Nothing to save: give content, shared or title")
    if is_over(row):
        if not row.get("ended_at"):
            # Past its limit: keep the record as ended, at the moment the limit was reached.
            limit = (_parse(row["created_at"]) + MAX_SESSION).isoformat()
            ctx.client.table("live_notes").update({"ended_at": limit}).eq("id", params.id).execute()
        raise HTTPException(409, "That session has ended, so it can't be changed; start_live_note opens a new one")
    changes["updated_at"] = _stamp()
    ctx.client.table("live_notes").update(changes).eq("id", params.id).execute()
    return {"id": params.id, "shared": changes.get("shared", row["shared"]), "updated_at": changes["updated_at"]}


class NoteIdParams(BaseModel):
    id: int = Field(..., description="The live note's id, from list_live_notes.")


@action(
    name="end_live_note",
    description="End a live note session: the class sees it is over, and it stays as a record anyone it was shared with can still read. Only the author can. Ending twice does nothing.",
    params=NoteIdParams,
    path="/live/end",
)
def end_live_note(ctx: Context, params: NoteIdParams):
    row = _own(ctx, params.id)
    if is_over(row):
        return {"id": params.id, "ended_at": row.get("ended_at") or (_parse(row["created_at"]) + MAX_SESSION).isoformat()}
    now = _stamp()
    ctx.client.table("live_notes").update({"ended_at": now, "updated_at": now}).eq("id", params.id).execute()
    return {"id": params.id, "ended_at": now}


def _follow(ctx: Context, row: dict[str, Any]) -> list[str]:
    """Record this read (unless it is the author's) and return the ids following the session,
    most recent first. Old entries are dropped here, so nothing grows without a read."""
    now = time.monotonic()
    with _seen_lock:
        if not _is_author(ctx, row):
            _seen.setdefault(row["id"], {})[ctx.user_id] = now
        # Prune every session, so an ended one's readers don't linger.
        for note_id in list(_seen):
            seen = _seen[note_id]
            for user_id in [u for u, at in seen.items() if now - at > FOLLOW_WINDOW]:
                del seen[user_id]
            if not seen:
                del _seen[note_id]
        seen = _seen.get(row["id"], {})
        return sorted(seen, key=lambda u: -seen[u])


def _followers(ctx: Context, ids: list[str]) -> dict[str, Any]:
    """{followers: [{id, name}], followers_count}: only active members, at most MAX_FOLLOWERS
    of them named. followers_count is the whole number, and is only sent when it is larger."""
    if not ids:
        return {"followers": []}
    rows = ctx.client.table("profiles").select("id, name").in_("id", ids).eq("status", "active").execute().data
    by_id = {r["id"]: r.get("name") for r in rows}
    people = [{"id": i, "name": by_id[i]} for i in ids if i in by_id]
    out: dict[str, Any] = {"followers": people[:MAX_FOLLOWERS]}
    if len(people) > MAX_FOLLOWERS:
        out["followers_count"] = len(people)
    return out


class ReadParams(BaseModel):
    id: int = Field(..., description="The live note's id, from list_live_notes.")
    since: str | None = Field(None, description="The updated_at of the copy you already have. If the note hasn't changed since, you get a short 'unchanged' answer instead of the text.")


@action(
    name="read_live_note",
    read_only=True,
    tool=True,
    mcp=True,
    description="Read a live note: the text one classmate is writing (or wrote) during a class, with its title, author, and whether it is being written now. It is one person's notes and nobody has checked them. Also followers, the classmates reading it in the last few seconds, by name. Pass since (a previous updated_at) to poll: an unchanged note answers with {unchanged: true} and the followers, which change on their own. A note its author hasn't shared can only be read by the author.",
    params=ReadParams,
    method="GET",
    path="/live/note",
)
def read_live_note(ctx: Context, params: ReadParams):
    row = _find(ctx, params.id)
    if not row["shared"] and not _is_author(ctx, row):
        raise HTTPException(404, f"Live note {params.id} isn't shared with the class; list_live_notes shows what is")
    now = _now()
    live = is_live(row, now)
    followers = _followers(ctx, _follow(ctx, row))
    if params.since and params.since == row["updated_at"]:
        return {"id": row["id"], "unchanged": True, "updated_at": row["updated_at"], "live": live, "ended": is_over(row, now), **followers}
    return {**_shape(ctx, row, now), "content": row["content"], "unchanged": False, **followers}


@action(
    name="list_live_notes",
    read_only=True,
    tool=True,
    mcp=True,
    description="The class's live notes: sessions being written right now first (live: true), then earlier ones, newest first, each with its title, author's name, whether it is live, ended or yours, and a short preview of the latest text. Also current_class, the timetable slot on now, if any. Notes their author hasn't shared are left out, except your own. Read one with read_live_note.",
    method="GET",
    path="/live",
)
def list_live_notes(ctx: Context, params: None):
    rows = (
        ctx.client.table("live_notes")
        .select(SUMMARY_COLUMNS)
        .or_(f"shared.eq.true,author_id.eq.{ctx.user_id}")
        .order("updated_at", desc=True)
        .limit(LIST_LIMIT)
        .execute()
        .data
    )
    now = _now()
    notes = []
    for row in rows:
        text = (row.get("content") or "").strip()
        notes.append({**_shape(ctx, row, now), "preview": text[-PREVIEW_CHARS:]})
    # Live ones first; the rest keep their newest-first order.
    notes.sort(key=lambda n: not n["live"])
    return {"notes": notes, "current_class": current_class(ctx.client)}


@action(
    name="delete_live_note",
    requires_confirmation=True,
    description="Delete a live note for good. Only its author or an admin can; it can't be undone.",
    params=NoteIdParams,
    path="/live/delete",
)
def delete_live_note(ctx: Context, params: NoteIdParams):
    row = _find(ctx, params.id)
    if not _is_author(ctx, row) and (ctx.profile or {}).get("role") != "admin":
        raise HTTPException(403, "Only the author or an admin can delete a live note")
    ctx.client.table("live_notes").delete().eq("id", params.id).execute()
    return {"ok": True}
