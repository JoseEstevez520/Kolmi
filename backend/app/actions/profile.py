from fastapi import HTTPException
from postgrest.exceptions import APIError
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

    # The database decides the role and status, in one step under a lock: whoever signs up first
    # on an instance with no admin becomes one, let in at once; anyone else is a student, pending
    # while the class asks for approval. Two sign-ups at once can't both be the first admin.
    try:
        created = (
            ctx.client.rpc("sign_up_profile", {"p_id": ctx.user_id, "p_name": params.name})
            .execute()
            .data
        )
    except APIError as exc:
        if exc.code == "23505":  # the same account signing up twice at once
            raise HTTPException(409, "Profile already exists") from exc
        raise
    return created[0] if isinstance(created, list) else created
