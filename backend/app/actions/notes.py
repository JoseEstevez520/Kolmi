from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel

from ..auth import Context
from .registry import action


# Plain text, or Markdown from the notes editor; both reach the pass as written.
NoteFormat = Literal["text", "markdown"]


class CreateNoteParams(BaseModel):
    content: str
    format: NoteFormat = "text"
    node_id: int | None = None


class UpdateNoteParams(BaseModel):
    note_id: int
    content: str
    format: NoteFormat = "markdown"


class MyNotesParams(BaseModel):
    status: str | None = None


@action(
    name="create_note",
    description="Leave a note. It stays private until the daily pass.",
    params=CreateNoteParams,
    path="/notes",
)
def create_note(ctx: Context, params: CreateNoteParams):
    if not ctx.profile or not ctx.profile.get("approved"):
        raise HTTPException(403, "Profile not approved")

    row = {
        "user_id": ctx.user_id,
        "content": params.content,
        "format": params.format,
        "node_id": params.node_id,
    }
    return ctx.client.table("notes").insert(row).execute().data[0]


@action(
    name="update_note",
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

    data = {"content": params.content, "format": params.format}
    return (
        ctx.client.table("notes").update(data).eq("id", params.note_id).execute().data[0]
    )


@action(
    name="my_notes",
    description="List the current user's notes, newest first.",
    params=MyNotesParams,
    method="GET",
    path="/notes/mine",
)
def my_notes(ctx: Context, params: MyNotesParams | None):
    query = ctx.client.table("notes").select("*").eq("user_id", ctx.user_id)
    if params and params.status:
        query = query.eq("status", params.status)
    return query.order("created_at", desc=True).execute().data
