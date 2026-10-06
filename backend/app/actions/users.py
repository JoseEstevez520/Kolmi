"""The class's people: an admin's list of them, their role and status, and taking someone out; and
a member's own name and account. Never over the MCP."""

import logging
from collections import Counter
from typing import Any, Literal

from fastapi import HTTPException
from pydantic import BaseModel, Field, field_validator

from ..auth import Context, forget_profile, on_access_lost, status_of
from ..files import BUCKET
from .registry import action

log = logging.getLogger(__name__)

PROFILE_COLUMNS = "id, name, role, status, created_at"
# Storage takes a list of keys per call; past a class's size, they go in batches.
REMOVE_BATCH = 100


class UserIdParams(BaseModel):
    user_id: str = Field(..., description="The person's id, from list_users.")


class SetRoleParams(UserIdParams):
    role: Literal["student", "admin"] = Field(
        ..., description="admin: they also manage the tree, the notes, the pass and the class's people. student: they read and leave notes."
    )


class SetStatusParams(UserIdParams):
    status: Literal["active", "pending", "blocked"] = Field(
        ..., description="active lets them in (to approve someone pending, too); blocked stops everything they do; pending puts them back to wait."
    )


class NameParams(BaseModel):
    name: str = Field(..., min_length=1, max_length=80, description="The name the class sees.")

    @field_validator("name")
    @classmethod
    def _trimmed(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("the name can't be blank")
        return value


def _profile(client, user_id: str) -> dict[str, Any]:
    rows = client.table("profiles").select(PROFILE_COLUMNS).eq("id", user_id).limit(1).execute().data
    if not rows:
        raise HTTPException(404, f"There is no user {user_id}; list_users lists the class")
    return rows[0]


def _is_active_admin(profile: dict[str, Any]) -> bool:
    return profile.get("role") == "admin" and status_of(profile) == "active"


def _keep_an_admin(client, target: dict[str, Any], doing: str) -> None:
    """Refuse to take away the last active admin: the class would have nobody to let people in.
    `doing` finishes "they can't be ...", or is "own" for someone deleting their own account."""
    if not _is_active_admin(target):
        return
    admins = client.table("profiles").select("id, role, status").eq("role", "admin").execute().data
    if sum(1 for row in admins if _is_active_admin(row)) > 1:
        return
    if doing == "own":
        reason = "You're the class's last admin, so you can't delete your account"
    else:
        reason = f"{target.get('name') or 'They'} is the class's last admin, so they can't be {doing}"
    raise HTTPException(409, f"{reason}: make someone else an admin first, then try again.")


def _emails(client) -> dict[str, str]:
    """Each account's email, from Supabase Auth; none when it can't be read, so the list still shows."""
    try:
        users = client.auth.admin.list_users(page=1, per_page=1000)
    except Exception as exc:
        log.warning("could not read the accounts' emails: %s", exc)
        return {}
    return {str(user.id): user.email for user in users if getattr(user, "email", None)}


def _delete_account(client, user_id: str) -> None:
    """Take an account out cleanly. Its notes' files go from Storage first; then the account goes
    from Supabase Auth, and the database follows: the profile, its notes and its chat cascade, a
    file on a shared page stays with no author. A processed note's content is in its page already."""
    notes = client.table("notes").select("id").eq("user_id", user_id).execute().data
    note_ids = [row["id"] for row in notes]
    paths: list[str] = []
    if note_ids:
        files = client.table("files").select("id, path").in_("note_id", note_ids).execute().data
        paths = [row["path"] for row in files if row.get("path")]
    try:
        for start in range(0, len(paths), REMOVE_BATCH):
            client.storage.from_(BUCKET).remove(paths[start : start + REMOVE_BATCH])
    except Exception as exc:
        raise HTTPException(502, "Could not remove their notes' files, so nothing was deleted; try again") from exc

    on_access_lost(user_id, client)
    try:
        client.auth.admin.delete_user(user_id)
    except Exception as exc:
        raise HTTPException(
            502, "Their notes' files are gone but the account could not be deleted; try again"
        ) from exc


@action(
    name="list_users",
    read_only=True,
    tool=True,
    description="The class's people: each one's id, name, email, role (student or admin), status (active, pending or blocked), when they joined and how many notes they have left. Admin only. Pending ones are waiting to be let in with set_status.",
    method="GET",
    path="/users",
    min_role="admin",
)
def list_users(ctx: Context, params: None):
    profiles = ctx.client.table("profiles").select(PROFILE_COLUMNS).order("created_at").execute().data
    notes = Counter(row["user_id"] for row in ctx.client.table("notes").select("user_id").execute().data)
    emails = _emails(ctx.client)
    return [
        {**row, "status": status_of(row), "email": emails.get(str(row["id"])), "notes": notes.get(row["id"], 0)}
        for row in profiles
    ]


@action(
    name="set_role",
    tool=True,
    description="Make someone an admin, or a student again. Admin only. The class always keeps an admin: the last one can't be made a student.",
    params=SetRoleParams,
    path="/users/role",
    min_role="admin",
)
def set_role(ctx: Context, params: SetRoleParams):
    target = _profile(ctx.client, params.user_id)
    if target.get("role") == params.role:
        return target
    if params.role == "student":
        _keep_an_admin(ctx.client, target, "made a student")
    rows = ctx.client.table("profiles").update({"role": params.role}).eq("id", params.user_id).execute().data
    if params.role == "student":
        on_access_lost(params.user_id, ctx.client)
    else:
        forget_profile(params.user_id)
    return rows[0] if rows else {**target, "role": params.role}


@action(
    name="set_status",
    tool=True,
    description="Let someone in (active, also to approve a pending sign-up), block them (blocked: they can do nothing), or put them back to wait (pending). Admin only. The class always keeps an active admin: the last one can't be blocked or put to wait.",
    params=SetStatusParams,
    path="/users/status",
    min_role="admin",
)
def set_status(ctx: Context, params: SetStatusParams):
    target = _profile(ctx.client, params.user_id)
    if status_of(target) == params.status:
        return target
    if params.status != "active":
        _keep_an_admin(ctx.client, target, "blocked" if params.status == "blocked" else "put to wait")
    rows = ctx.client.table("profiles").update({"status": params.status}).eq("id", params.user_id).execute().data
    if params.status == "active":
        forget_profile(params.user_id)
    else:
        on_access_lost(params.user_id, ctx.client)
    return rows[0] if rows else {**target, "status": params.status}


@action(
    name="delete_user",
    tool=True,
    description="Delete someone's account: they leave the class, with their notes, their notes' files and their chat. What the pass already wrote into the pages stays, and so do the files on shared pages, with no author. Admin only, confirmed, and it can't be undone; to only stop them, set_status blocked. The last admin can't be deleted.",
    params=UserIdParams,
    path="/users/delete",
    requires_confirmation=True,
    min_role="admin",
)
def delete_user(ctx: Context, params: UserIdParams):
    target = _profile(ctx.client, params.user_id)
    _keep_an_admin(ctx.client, target, "deleted")
    _delete_account(ctx.client, params.user_id)
    return {"deleted": params.user_id}


@action(
    name="update_my_name",
    tool=True,
    description="Change your own name, the one the class sees.",
    params=NameParams,
    path="/profile/name",
)
def update_my_name(ctx: Context, params: NameParams):
    rows = ctx.client.table("profiles").update({"name": params.name}).eq("id", ctx.user_id).execute().data
    forget_profile(ctx.user_id)
    if not rows:
        raise HTTPException(404, "Profile not found")
    return rows[0]


@action(
    name="delete_my_account",
    description="Delete your own account: your notes, their files and your chat go; what the pass already wrote into the pages stays. Confirmed, and it can't be undone.",
    path="/profile/delete",
    requires_confirmation=True,
    any_status=True,
)
def delete_my_account(ctx: Context, params: None):
    if ctx.profile:
        _keep_an_admin(ctx.client, ctx.profile, "own")
    _delete_account(ctx.client, ctx.user_id)
    return {"deleted": ctx.user_id}
