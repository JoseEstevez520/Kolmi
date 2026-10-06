from fastapi import HTTPException
from pydantic import BaseModel

from ..auth import Context
from ..files import (
    BUCKET,
    DOWNLOAD_URL_SECONDS,
    files_guard,
    is_admin,
    own_pending_note,
    read_access,
)
from .registry import action

COLUMNS = "id, node_id, note_id, name, size, mime, user_id, created_at"


class NoteFilesParams(BaseModel):
    note_id: int


class FileIdParams(BaseModel):
    file_id: int


def _file(ctx: Context, file_id: int) -> dict:
    with files_guard():
        rows = (
            ctx.client.table("files").select(f"{COLUMNS}, path").eq("id", file_id).limit(1)
            .execute().data
        )
    if not rows:
        raise HTTPException(404, "File not found")
    return rows[0]


@action(
    name="note_files",
    read_only=True,
    description="List the files attached to one of your notes.",
    params=NoteFilesParams,
    method="GET",
    path="/files",
)
def note_files(ctx: Context, params: NoteFilesParams):
    if not is_admin(ctx):
        # Someone else's note answers as a missing one.
        rows = (
            ctx.client.table("notes").select("id, user_id").eq("id", params.note_id).limit(1)
            .execute().data
        )
        if not rows or rows[0]["user_id"] != ctx.user_id:
            raise HTTPException(404, "Note not found")
    with files_guard():
        return (
            ctx.client.table("files").select(COLUMNS).eq("note_id", params.note_id).order("id")
            .execute().data
        )


@action(
    name="download_file",
    read_only=True,
    description="A short-lived link to download a file.",
    params=FileIdParams,
    method="GET",
    path="/files/download",
)
def download_file(ctx: Context, params: FileIdParams):
    file = _file(ctx, params.file_id)
    read_access(ctx, file)
    with files_guard():
        signed = ctx.client.storage.from_(BUCKET).create_signed_url(
            file["path"], DOWNLOAD_URL_SECONDS, {"download": file["name"]}
        )
    return {"url": signed.get("signedURL") or signed.get("signedUrl"), "name": file["name"]}


@action(
    name="delete_file",
    description="Remove a file: one of a page (admin) or one on your own pending note.",
    params=FileIdParams,
    path="/files/delete",
)
def delete_file(ctx: Context, params: FileIdParams):
    file = _file(ctx, params.file_id)
    if file.get("node_id") is not None:
        if not is_admin(ctx):
            raise HTTPException(403, "Admin only")
    elif not is_admin(ctx):
        own_pending_note(ctx, file["note_id"])

    with files_guard():
        ctx.client.storage.from_(BUCKET).remove([file["path"]])
        ctx.client.table("files").delete().eq("id", params.file_id).execute()
    return {"ok": True}
