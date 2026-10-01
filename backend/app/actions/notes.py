from fastapi import HTTPException
from pydantic import BaseModel

from ..auth import Context
from .registry import action


class CreateNoteParams(BaseModel):
    content: str
    module_id: int | None = None
    page_id: int | None = None


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
        "module_id": params.module_id,
        "page_id": params.page_id,
    }
    return ctx.client.table("notes").insert(row).execute().data[0]


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
