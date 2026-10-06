from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel, Field

from postgrest.exceptions import APIError

from ..auth import Context
from ..class_settings import read_settings
from ..files import BUCKET, is_missing, own_pending_note
from ..passes.schedule import today_start
from .registry import action


# Plain text, or Markdown from the notes editor; both reach the pass as written.
NoteFormat = Literal["text", "markdown"]


class CreateNoteParams(BaseModel):
    content: str = Field("", description="The note, as Markdown or plain text.")
    # A note with neither text nor files is never kept. Attaching a file to a note not written
    # yet creates it empty, and its file follows at once: this says that is what is happening.
    for_files: bool = Field(False, description="Leave it false: only the web sets it, to create an empty note its files follow.")
    format: NoteFormat = Field("text", description="markdown or text.")
    node_id: int | None = Field(None, description="Optional: the section or page it seems to belong to, from list_nodes. A hint, not an order.")
    source_url: str | None = Field(None, description="Optional: the address of the page or document the note comes from, if it does.")


class UpdateNoteParams(BaseModel):
    note_id: int = Field(..., description="The note's id, from my_notes.")
    content: str = Field(..., description="The new text; it replaces the whole note.")
    format: NoteFormat = Field("markdown", description="markdown or text.")
    # Left out, the hint stays as it was; null clears it.
    node_id: int | None = Field(None, description="Optional: the section or page it seems to belong to, from list_nodes. Left out, the hint stays; null clears it.")


def _check_hint(ctx: Context, node_id: int | None) -> None:
    """The hint, where the student thinks the note goes, must be a node of the tree."""
    if node_id is None:
        return
    found = ctx.client.table("nodes").select("id").eq("id", node_id).limit(1).execute().data
    if not found:
        raise HTTPException(422, f"There is no node {node_id}; list_nodes shows the tree")


def _has_files(ctx: Context, note_id: int) -> bool:
    try:
        rows = ctx.client.table("files").select("id").eq("note_id", note_id).limit(1).execute().data
    except APIError as exc:
        # Files are not set up yet: there are none.
        if is_missing(exc):
            return False
        raise
    return bool(rows)


def _with_file_names(ctx: Context, notes: list[dict]) -> list[dict]:
    """Each note with the names of its files, so a note of only files can be told apart."""
    for note in notes:
        note["files"] = []
    if not notes:
        return notes
    try:
        rows = (
            ctx.client.table("files").select("id, note_id, name, size")
            .in_("note_id", [n["id"] for n in notes]).order("id").execute().data
        )
    except APIError as exc:
        if is_missing(exc):
            return notes
        raise
    by_id = {n["id"]: n for n in notes}
    for row in rows:
        by_id[row["note_id"]]["files"].append({"id": row["id"], "name": row["name"], "size": row["size"]})
    return notes


class MyNotesParams(BaseModel):
    status: str | None = Field(None, description="Only the notes with this status: pending, processed or discarded.")


def _within_the_mcp_cap(ctx: Context) -> None:
    """A student's own AI leaves at most the class's daily number of notes: each one costs the
    gatekeeper a call. Admins have no cap, and the app has none."""
    if ctx.source != "mcp" or (ctx.profile or {}).get("role") == "admin":
        return
    cap = read_settings(ctx.client).get("mcp_daily_notes", 30)
    left = (
        ctx.client.table("notes")
        .select("id", count="exact")
        .eq("user_id", ctx.user_id)
        .eq("source", "mcp")
        .gte("created_at", today_start())
        .execute()
    )
    if (left.count or 0) >= cap:
        raise HTTPException(
            429,
            f"You've left {cap} notes through your AI today, the most a day in this class. You can "
            "leave more from midnight (Madrid time), or write them in the app.",
        )


@action(
    name="create_note",
    tool=True,
    mcp=True,
    description="Leave a note for the class: something learned, a correction, a summary of a source. It stays private until the daily pass, which writes it into the page it belongs to, or discards it with a reason. One note per topic. Not for questions: those go to the chat.",
    params=CreateNoteParams,
    path="/notes",
)
def create_note(ctx: Context, params: CreateNoteParams):
    _check_hint(ctx, params.node_id)
    if not params.content.strip() and not params.for_files:
        raise HTTPException(422, "A note needs some text or a file")
    _within_the_mcp_cap(ctx)

    row = {
        "user_id": ctx.user_id,
        "content": params.content,
        "format": params.format,
        "node_id": params.node_id,
        "source": ctx.source,
    }
    if params.source_url:
        row["source_url"] = params.source_url
    return ctx.client.table("notes").insert(row).execute().data[0]


@action(
    name="update_note",
    tool=True,
    mcp=True,
    description="Rewrite one of your own notes while it is still pending; the daily pass takes it as it is then. The text given replaces the whole note. Find its id with my_notes.",
    params=UpdateNoteParams,
    path="/notes/update",
)
def update_note(ctx: Context, params: UpdateNoteParams):
    rows = (
        ctx.client.table("notes")
        .select("id, user_id, status")
        .eq("id", params.note_id)
        .limit(1)
        .execute()
        .data
    )
    # Someone else's note answers as a missing one: it says nothing about it.
    if not rows or rows[0]["user_id"] != ctx.user_id:
        raise HTTPException(404, f"You have no note {params.note_id}; my_notes lists yours")
    if rows[0]["status"] != "pending":
        raise HTTPException(409, "The daily pass already took this note; leave a new one with create_note")

    if not params.content.strip() and not _has_files(ctx, params.note_id):
        raise HTTPException(422, "A note needs some text or a file")

    data = {"content": params.content, "format": params.format}
    if "node_id" in params.model_fields_set:
        _check_hint(ctx, params.node_id)
        data["node_id"] = params.node_id
    return (
        ctx.client.table("notes").update(data).eq("id", params.note_id).execute().data[0]
    )


@action(
    name="my_notes",
    read_only=True,
    tool=True,
    mcp=True,
    description="Your own notes, newest first, each with its status (pending, processed or discarded) and its files' names. Use it to find a note to edit, or to see what the daily pass did with one.",
    params=MyNotesParams,
    method="GET",
    path="/notes/mine",
)
def my_notes(ctx: Context, params: MyNotesParams | None):
    query = ctx.client.table("notes").select("*").eq("user_id", ctx.user_id)
    if params and params.status:
        query = query.eq("status", params.status)
    notes = query.order("created_at", desc=True).execute().data
    return _with_file_names(ctx, notes)


class NoteIdParams(BaseModel):
    note_id: int = Field(..., description="The note's id, from my_notes.")


@action(
    name="delete_note",
    tool=True,
    mcp=True,
    description="Delete one of your own notes while it is still pending, with its files. Confirmed, and it can't be undone. Once the daily pass has taken a note it is part of a page, and stays.",
    params=NoteIdParams,
    path="/notes/delete",
    requires_confirmation=True,
)
def delete_note(ctx: Context, params: NoteIdParams):
    own_pending_note(ctx, params.note_id)
    try:
        files = ctx.client.table("files").select("path").eq("note_id", params.note_id).execute().data
    except APIError as exc:
        if not is_missing(exc):  # files are not set up yet: there are none
            raise
        files = []
    paths = [row["path"] for row in files if row.get("path")]
    if paths:
        ctx.client.storage.from_(BUCKET).remove(paths)
    ctx.client.table("notes").delete().eq("id", params.note_id).execute()
    return {"deleted": params.note_id}


class SearchParams(BaseModel):
    query: str = Field(..., min_length=2, max_length=200, description="Words to look for in the pages' titles and text.")


# Enough to tell the hits apart and pick one to read with view_node.
SEARCH_LIMIT = 20
SNIPPET = 160


def _snippet(text: str, at: int) -> str:
    start = max(at - SNIPPET // 2, 0)
    part = text[start : start + SNIPPET].replace("\n", " ").strip()
    return ("…" if start else "") + part + ("…" if start + SNIPPET < len(text) else "")


@action(
    name="search_pages",
    read_only=True,
    tool=True,
    mcp=True,
    description="Look for words in the class's pages: their titles and their Markdown. Each hit gives the page's id, its title and a bit of text round the words, best first; read the page with view_node. For where something belongs in the tree, list_nodes.",
    params=SearchParams,
    method="GET",
    path="/search",
)
def search_pages(ctx: Context, params: SearchParams):
    # A class's pages are few: they are read once and matched here, every word in the title or
    # the text, the title's hits first.
    words = [w for w in params.query.lower().split() if w]
    pages = ctx.client.table("nodes").select("id, title, kind, content_md").eq("kind", "page").execute().data
    hits = []
    for page in pages:
        title, text = (page.get("title") or ""), (page.get("content_md") or "")
        low_title, low_text = title.lower(), text.lower()
        if not all(w in low_title or w in low_text for w in words):
            continue
        in_title = sum(w in low_title for w in words)
        at = min((low_text.find(w) for w in words if w in low_text), default=0)
        hits.append((-in_title, title, {"id": page["id"], "title": title, "snippet": _snippet(text, at)}))
    hits.sort(key=lambda hit: hit[:2])
    return [hit[2] for hit in hits[:SEARCH_LIMIT]]
