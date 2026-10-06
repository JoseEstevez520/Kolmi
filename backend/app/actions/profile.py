from fastapi import HTTPException
from pydantic import BaseModel

from ..auth import Context
from ..class_settings import read_settings
from ..config import get_settings
from .registry import action


class RegisterProfileParams(BaseModel):
    code: str
    name: str


@action(
    name="get_profile",
    read_only=True,
    any_status=True,
    description="Get the current user's profile. 404 if it doesn't exist yet.",
    method="GET",
    path="/profile",
)
def get_profile(ctx: Context, params: None):
    if not ctx.profile:
        raise HTTPException(404, "Profile not found")
    return ctx.profile


@action(
    name="register_profile",
    description="Create the current user's profile using the class code.",
    params=RegisterProfileParams,
    path="/register",
    any_status=True,
)
def register_profile(ctx: Context, params: RegisterProfileParams):
    if ctx.profile:
        raise HTTPException(409, "Profile already exists")
    if params.code != get_settings().class_code:
        raise HTTPException(403, "Wrong class code")

    # An address in ADMIN_EMAILS signs up as an admin, let in at once: that is how a class gets
    # its first one. Anyone else waits for an admin while the class asks for approval.
    if (ctx.email or "").strip().lower() in get_settings().admin_emails_set:
        row = {"role": "admin", "status": "active"}
    elif read_settings(ctx.client).get("signups_need_approval"):
        row = {"role": "student", "status": "pending"}
    else:
        row = {"role": "student", "status": "active"}

    rows = (
        ctx.client.table("profiles")
        .insert({"id": ctx.user_id, "name": params.name, **row})
        .execute()
        .data
    )
    return rows[0]
