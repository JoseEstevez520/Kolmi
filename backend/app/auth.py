from dataclasses import dataclass
from typing import Any

from fastapi import Depends, Header, HTTPException, status
from supabase import Client

from .supabase_client import get_client


@dataclass
class Context:
    """Who is calling, and with which client.

    Everything an action needs to run. The chat, later, will build the same
    context for the user it is acting as.
    """

    user_id: str
    email: str | None
    profile: dict[str, Any] | None
    client: Client


def _bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    return authorization.split(" ", 1)[1].strip()


def get_context(
    authorization: str | None = Header(default=None),
    client: Client = Depends(get_client),
) -> Context:
    """Validate the Supabase access token and load the caller's profile."""
    token = _bearer_token(authorization)

    try:
        response = client.auth.get_user(token)
    except Exception as exc:  # invalid or expired token
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token") from exc

    user = getattr(response, "user", None)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

    rows = (
        client.table("profiles").select("*").eq("id", user.id).limit(1).execute().data
    )
    profile = rows[0] if rows else None

    return Context(
        user_id=user.id,
        email=getattr(user, "email", None),
        profile=profile,
        client=client,
    )
