"""The upload route. The file is the request's body, so it needs no multipart parser."""

from fastapi import APIRouter, Depends, HTTPException, Request

from .auth import Context, app_only, check_active, get_context
from .files import (
    BUCKET,
    MAX_FILE_BYTES,
    MAX_FILES_PER_NOTE,
    check_file,
    files_guard,
    is_admin,
    object_key,
    own_pending_note,
    stored_mime,
)

router = APIRouter()


async def _body(request: Request) -> bytes:
    """The whole body, refused as soon as it is past the limit."""
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > MAX_FILE_BYTES:
        raise HTTPException(413, f"Files can be up to {MAX_FILE_BYTES // (1024 * 1024)} MB")
    data = bytearray()
    async for chunk in request.stream():
        data += chunk
        if len(data) > MAX_FILE_BYTES:
            raise HTTPException(413, f"Files can be up to {MAX_FILE_BYTES // (1024 * 1024)} MB")
    return bytes(data)


def store_upload(
    ctx: Context, *, name: str, mime: str, data: bytes,
    note_id: int | None = None, node_id: int | None = None,
) -> dict:
    """Check who is sending what, keep it in the bucket and record it."""
    check_active(ctx)
    app_only(ctx)
    if (note_id is None) == (node_id is None):
        raise HTTPException(422, "Give a note_id or a node_id")
    name = (name or "").strip().replace("\\", "/").split("/")[-1][:200]
    if not name:
        raise HTTPException(422, "The file needs a name")

    if note_id is not None:
        own_pending_note(ctx, note_id)
    else:
        if not is_admin(ctx):
            raise HTTPException(403, "Admin only")
        if not ctx.client.table("nodes").select("id").eq("id", node_id).limit(1).execute().data:
            raise HTTPException(404, "Node not found")

    check_file(name, mime, len(data), data)
    mime = stored_mime(name, mime)

    with files_guard():
        if note_id is not None:
            held = ctx.client.table("files").select("id").eq("note_id", note_id).execute().data
            if len(held) >= MAX_FILES_PER_NOTE:
                raise HTTPException(409, f"A note can carry {MAX_FILES_PER_NOTE} files")
        path = object_key(f"notes/{note_id}" if note_id is not None else f"nodes/{node_id}", name)
        bucket = ctx.client.storage.from_(BUCKET)
        bucket.upload(path, data, {"content-type": mime, "upsert": "false"})
        row = {
            "node_id": node_id, "note_id": note_id, "name": name, "size": len(data),
            "mime": mime, "path": path, "user_id": ctx.user_id,
        }
        try:
            saved = ctx.client.table("files").insert(row).execute().data[0]
        except Exception:
            bucket.remove([path])
            raise
    saved.pop("path", None)
    return saved


@router.post("/files/upload", summary="Attach a file to a note (its author) or a page (admin).")
async def upload(
    request: Request,
    name: str,
    note_id: int | None = None,
    node_id: int | None = None,
    ctx: Context = Depends(get_context),
):
    mime = request.headers.get("content-type", "")
    # Who and what first, so a stranger's body is never read; the body is checked again in full.
    check_file(name, mime, 1)
    data = await _body(request)
    return store_upload(ctx, name=name, mime=mime, data=data, note_id=note_id, node_id=node_id)
