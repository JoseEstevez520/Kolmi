"""The profile photo routes. The image is the request's body, as with files; it is always one's own."""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request

from .auth import Context, app_only, check_active, forget_profile, get_context
from .avatars import BUCKET, MAX_AVATAR_BYTES, avatar_url, image_mime

router = APIRouter()
log = logging.getLogger(__name__)

TOO_BIG = f"A photo can be up to {MAX_AVATAR_BYTES // 1024} KB"


async def _body(request: Request) -> bytes:
    """The whole body, refused as soon as it is past the limit."""
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > MAX_AVATAR_BYTES:
        raise HTTPException(413, TOO_BIG)
    data = bytearray()
    async for chunk in request.stream():
        data += chunk
        if len(data) > MAX_AVATAR_BYTES:
            raise HTTPException(413, TOO_BIG)
    return bytes(data)


def _current(ctx: Context) -> str | None:
    rows = ctx.client.table("profiles").select("avatar_path").eq("id", ctx.user_id).limit(1).execute().data
    return rows[0].get("avatar_path") if rows else None


def _drop(ctx: Context, path: str | None) -> None:
    """Remove an old object. Best effort: a photo left behind is only an unused file."""
    if not path:
        return
    try:
        ctx.client.storage.from_(BUCKET).remove([path])
    except Exception:
        log.warning("Could not remove an old avatar object", exc_info=True)


def set_avatar(ctx: Context, data: bytes) -> dict:
    """Check who is sending what, keep it in the bucket and point the profile at it."""
    check_active(ctx)
    app_only(ctx)
    if not data:
        raise HTTPException(422, "The photo is empty")
    if len(data) > MAX_AVATAR_BYTES:
        raise HTTPException(413, TOO_BIG)
    mime = image_mime(data)
    if mime is None:
        raise HTTPException(415, "The photo has to be a JPEG, PNG or WebP image")

    old = _current(ctx)
    path = f"{uuid.uuid4().hex}.jpg"
    bucket = ctx.client.storage.from_(BUCKET)
    bucket.upload(path, data, {"content-type": mime, "upsert": "false"})
    try:
        ctx.client.table("profiles").update({"avatar_path": path}).eq("id", ctx.user_id).execute()
    except Exception:
        _drop(ctx, path)
        raise
    forget_profile(ctx.user_id)
    _drop(ctx, old)
    return {"avatar_url": avatar_url(path)}


def clear_avatar(ctx: Context) -> dict:
    check_active(ctx)
    app_only(ctx)
    old = _current(ctx)
    ctx.client.table("profiles").update({"avatar_path": None}).eq("id", ctx.user_id).execute()
    forget_profile(ctx.user_id)
    _drop(ctx, old)
    return {"avatar_url": None}


@router.post("/profile/avatar", summary="Set your own profile photo (a JPEG, PNG or WebP, up to 512 KB).")
async def upload_avatar(request: Request, ctx: Context = Depends(get_context)):
    # Who first, so a stranger's body is never read.
    check_active(ctx)
    app_only(ctx)
    return set_avatar(ctx, await _body(request))


@router.delete("/profile/avatar", summary="Remove your own profile photo.")
def delete_avatar(ctx: Context = Depends(get_context)):
    return clear_avatar(ctx)
