"""Personal tokens: how a member's own AI acts as them over the MCP.

A token is `kolmi_` and 32 random bytes (256 bits) from `secrets`, shown once when it is made.
Only its SHA-256 hash is kept: a token this long can't be guessed, so a slow password hash buys
nothing, and a plain hash lets a request be checked with one lookup. A short prefix tells tokens
apart in a list. A token never goes into a log, an error or a tool's answer.
"""

from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import datetime, timezone
from typing import Any

log = logging.getLogger(__name__)

PREFIX = "kolmi_"
# Enough of the token to tell one from another in a list, and nothing more.
SHOWN = len(PREFIX) + 6
COLUMNS = "id, name, prefix, last_used_at, created_at, revoked_at"


def is_token(value: str) -> bool:
    return value.startswith(PREFIX)


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create(client, user_id: str, name: str) -> dict[str, Any]:
    """Make a token for `user_id`. The answer is the only time the token itself is seen."""
    token = PREFIX + secrets.token_urlsafe(32)
    row = (
        client.table("api_tokens")
        .insert({"user_id": user_id, "name": name, "token_hash": _hash(token), "prefix": token[:SHOWN]})
        .execute()
        .data[0]
    )
    return {**{key: row.get(key) for key in COLUMNS.split(", ")}, "token": token}


def owner(client, token: str) -> str | None:
    """The user a live token belongs to, or None for one that is unknown or revoked. Marks it used."""
    rows = (
        client.table("api_tokens")
        .select("id, user_id, revoked_at")
        .eq("token_hash", _hash(token))
        .limit(1)
        .execute()
        .data
    )
    if not rows or rows[0].get("revoked_at"):
        return None
    try:
        client.table("api_tokens").update({"last_used_at": _now()}).eq("id", rows[0]["id"]).execute()
    except Exception as exc:  # a missed "last used" never stops the request
        log.warning("could not mark token %s as used: %s", rows[0]["id"], exc)
    return rows[0]["user_id"]


def listed(client, user_id: str) -> list[dict[str, Any]]:
    return (
        client.table("api_tokens").select(COLUMNS).eq("user_id", user_id).order("created_at").execute().data
    )


def revoke(client, user_id: str, token_id: int) -> bool:
    """Revoke one of `user_id`'s tokens; False when they have no such token."""
    rows = (
        client.table("api_tokens")
        .update({"revoked_at": _now()})
        .eq("id", token_id)
        .eq("user_id", user_id)
        .is_("revoked_at", "null")
        .execute()
        .data
    )
    return bool(rows)


def revoke_all(client, user_id: str) -> None:
    """Revoke every live token of `user_id`: they lost their access."""
    client.table("api_tokens").update({"revoked_at": _now()}).eq("user_id", user_id).is_(
        "revoked_at", "null"
    ).execute()
