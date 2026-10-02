import time
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


# A profile read lately, by user id, so a page that makes a few requests reads it once. Only
# found profiles are kept: someone who just registered is seen at once. A change of role or
# approval reaches the API within PROFILE_TTL seconds.
PROFILE_TTL = 30.0
_profiles: dict[str, tuple[float, dict[str, Any]]] = {}


def _profile(client: Client, user_id: str) -> dict[str, Any] | None:
    cached = _profiles.get(user_id)
    if cached and time.monotonic() - cached[0] < PROFILE_TTL:
        return cached[1]

    rows = client.table("profiles").select("*").eq("id", user_id).limit(1).execute().data
    if not rows:
        _profiles.pop(user_id, None)
        return None
    _profiles[user_id] = (time.monotonic(), rows[0])
    return rows[0]


def get_context(
    authorization: str | None = Header(default=None),
    client: Client = Depends(get_client),
) -> Context:
    """Validate the Supabase access token and load the caller's profile.

    The token is checked here, against the project's public signing keys (fetched once and
    cached by the client), instead of asking Supabase on every request. A token signed the
    old way (HS256) still goes to Supabase.
    """
    token = _bearer_token(authorization)

    try:
        response = client.auth.get_claims(token)
    except Exception as exc:  # invalid, expired or forged token
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token") from exc

    claims = response["claims"] if response else None
    user_id = claims.get("sub") if claims else None
    if not user_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

    return Context(
        user_id=user_id,
        email=claims.get("email"),
        profile=_profile(client, user_id),
        client=client,
    )
