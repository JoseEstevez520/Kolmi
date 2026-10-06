from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel

from postgrest.exceptions import APIError

from ..auth import Context
from ..files import is_missing
from .registry import action


# Plain text, or Markdown from the notes editor; both reach the pass as written.
NoteFormat = Literal["text", "markdown"]


class CreateNoteParams(BaseModel):
    content: str = ""
    # A note with neither text nor files is never kept. Attaching a file to a note not written
    # yet creates it empty, and its file follows at once: this says that is what is happening.
    for_files: bool = False
    format: NoteFormat = "text"
    node_id: int | None = None


class UpdateNoteParams(BaseModel):
    note_id: int
    content: str
    format: NoteFormat = "markdown"
    # Left out, the hint stays as it was; null clears it.
    node_id: int | None = None


def _check_hint(ctx: Context, node_id: int | None) -> None:
    """The hint, where the student thinks the note goes, must be a node of the tree."""
    if node_id is None:
        return
    found = ctx.client.table("nodes").select("id").eq("id", node_id).limit(1).execute().data
    if not found:
        raise HTTPException(422, "That section or page does not exist")


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
    status: str | None = None


@action(
    name="create_note",
    tool=True,
    mcp=True,
    description="Leave a note. It stays private until the daily pass.",
    params=CreateNoteParams,
    path="/notes",
)
def create_note(ctx: Context, params: CreateNoteParams):
    if not ctx.profile or not ctx.profile.get("approved"):
        raise HTTPException(403, "Profile not approved")
    _check_hint(ctx, params.node_id)
    if not params.content.strip() and not params.for_files:
        raise HTTPException(422, "A note needs some text or a file")

    row = {
        "user_id": ctx.user_id,
        "content": params.content,
        "format": params.format,
        "node_id": params.node_id,
    }
    return ctx.client.table("notes").insert(row).execute().data[0]


@action(
    name="update_note",
    tool=True,
    mcp=True,
    description="Rewrite one of your notes. Only until the daily pass takes it.",
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
        raise HTTPException(404, "Note not found")
    if rows[0]["status"] != "pending":
        raise HTTPException(409, "The daily pass already took this note")

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
    description="List the current user's notes, newest first.",
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
