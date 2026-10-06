from fastapi import HTTPException
from pydantic import BaseModel

from ..auth import Context
from ..config import get_settings
from .registry import action


class RegisterProfileParams(BaseModel):
    code: str
    name: str


@action(
    name="get_profile",
    read_only=True,
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
)
def register_profile(ctx: Context, params: RegisterProfileParams):
    if ctx.profile:
        raise HTTPException(409, "Profile already exists")
    if params.code != get_settings().class_code:
        raise HTTPException(403, "Wrong class code")

    rows = (
        ctx.client.table("profiles")
        .insert({"id": ctx.user_id, "name": params.name})
        .execute()
        .data
    )
    return rows[0]
