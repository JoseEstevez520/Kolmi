"""Who may do anything at all: the status checked once in invoke, sign-up, and the cached profile."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException
from postgrest.exceptions import APIError

from app import auth
from app.actions import get_registry, invoke
from app.auth import Context, check_active, forget_profile, on_access_lost, status_of
from app.config import get_settings
from tests.test_content import _Table


class _Settings(_Table):
    def upsert(self, row: dict[str, Any]):
        return self.insert(row)


class _Client:
    def __init__(self, **tables: list[dict[str, Any]]) -> None:
        self.tables: dict[str, list[dict[str, Any]]] = {"profiles": [], "settings": [], **tables}

    def table(self, name: str) -> _Table:
        return (_Settings if name == "settings" else _Table)(self.tables.setdefault(name, []))


def _ctx(status: str | None = "active", role: str = "student", email: str | None = None, client=None):
    profile = None if status is None else {"id": "u1", "name": "Ana", "role": role, "status": status}
    return Context(user_id="u1", email=email, profile=profile, client=client or _Client())


def _refusal(ctx: Context, name: str = "list_nodes", args: dict[str, Any] | None = None) -> str:
    with pytest.raises(HTTPException) as err:
        invoke(get_registry()[name], ctx, args or {})
    assert err.value.status_code == 403
    return err.value.detail


# -- the status, once, in invoke ------------------------------------------------------------------


def test_an_active_member_reads():
    assert invoke(get_registry()["list_nodes"], _ctx(), {}) == []


def test_a_pending_member_is_told_to_wait_for_an_admin():
    assert _refusal(_ctx("pending")) == "Your account is pending: an admin has to let you in"


def test_a_blocked_member_is_told_so():
    assert _refusal(_ctx("blocked")) == "Your account is blocked: ask an admin of the class"


def test_no_profile_is_told_to_sign_up():
    assert "sign up with the class code" in _refusal(_ctx(None))


def test_a_blocked_admin_is_stopped_too():
    assert "blocked" in _refusal(_ctx("blocked", role="admin"), "list_users")


@pytest.mark.parametrize("name", ["list_nodes", "view_node", "my_notes", "create_note", "ask_chat"])
def test_a_pending_member_cannot_read_or_write(name):
    _refusal(_ctx("pending"), name, {"node_id": 1, "content": "x", "question": "x"})


def test_the_profile_is_open_whatever_the_status():
    for current in ("pending", "blocked"):
        assert invoke(get_registry()["get_profile"], _ctx(current), {})["status"] == current


def test_only_a_few_actions_run_whatever_the_status():
    allowed = {a.name for a in get_registry().values() if a.any_status}
    assert allowed == {"get_profile", "register_profile", "delete_my_account"}


def test_a_profile_from_before_the_migration_reads_its_approval():
    assert status_of({"approved": True}) == "active"
    assert status_of({"approved": False}) == "pending"
    assert status_of({"status": "blocked", "approved": True}) == "blocked"
    assert status_of(None) is None


def test_the_routes_that_are_not_actions_check_it_too():
    from app.export_api import export
    from app.files_api import store_upload

    with pytest.raises(HTTPException) as err:
        store_upload(_ctx("blocked"), name="a.pdf", mime="application/pdf", data=b"%PDF", note_id=1)
    assert err.value.status_code == 403
    with pytest.raises(HTTPException) as err:
        export(None, _ctx("pending"))
    assert err.value.status_code == 403


def test_check_active_lets_an_active_member_through():
    check_active(_ctx("active"))


# -- sign-up ---------------------------------------------------------------------------------------


class _Signups:
    """`sign_up_profile` as the database runs it (supabase/migrations/20261008120000_first_admin.sql):
    the first on an instance with no admin becomes one, active; anyone else a student, pending while
    approval is on. Whether two at once can both be first is the lock's job, checked on Postgres."""

    def __init__(self, client: "_Client") -> None:
        self.client = client
        self.calls: list[dict[str, Any]] = []

    def __call__(self, name: str, params: dict[str, Any]):
        assert name == "sign_up_profile"
        self.calls.append(params)
        profiles = self.client.tables["profiles"]
        if any(p["id"] == params["p_id"] for p in profiles):
            raise APIError({"code": "23505", "message": "duplicate key value"})
        settings = self.client.tables["settings"]
        waiting = bool(settings and settings[0].get("signups_need_approval"))
        if not any(p["role"] == "admin" for p in profiles):
            row = {"role": "admin", "status": "active"}
        else:
            row = {"role": "student", "status": "pending" if waiting else "active"}
        row = {"id": params["p_id"], "name": params["p_name"], **row}
        profiles.append(row)
        return SimpleNamespace(execute=lambda: SimpleNamespace(data=row))


def _signing_up(**tables) -> _Client:
    client = _Client(**tables)
    client.rpc = _Signups(client)
    return client


def _sign_up(client, user="u1", name="Ana"):
    ctx = Context(user_id=user, email=f"{user}@class.org", profile=None, client=client)
    return invoke(get_registry()["register_profile"], ctx, {"code": get_settings().class_code, "name": name})


APPROVAL_ON = [{"id": 1, "class_language": "en", "signups_need_approval": True}]


def test_the_first_to_sign_up_becomes_an_active_admin():
    row = _sign_up(_signing_up())

    assert row["role"] == "admin" and row["status"] == "active"


def test_the_first_admin_is_let_in_even_with_approval_on():
    row = _sign_up(_signing_up(settings=APPROVAL_ON))

    assert row["role"] == "admin" and row["status"] == "active"


def test_two_sign_ups_in_a_row_give_one_admin():
    client = _signing_up()

    first, second = _sign_up(client, "u1", "Ana"), _sign_up(client, "u2", "Sam")

    assert (first["role"], second["role"]) == ("admin", "student")
    assert second["status"] == "active"
    assert sum(p["role"] == "admin" for p in client.tables["profiles"]) == 1


def test_an_instance_with_an_admin_signs_up_a_student():
    client = _signing_up(profiles=[{"id": "a1", "name": "Ana", "role": "admin", "status": "active"}])

    row = _sign_up(client, "u2", "Sam")

    assert row["role"] == "student" and row["status"] == "active"


def test_with_approval_on_a_new_sign_up_waits():
    client = _signing_up(
        profiles=[{"id": "a1", "name": "Ana", "role": "admin", "status": "active"}], settings=APPROVAL_ON
    )

    row = _sign_up(client, "u2", "Sam")

    assert row["role"] == "student" and row["status"] == "pending"


def test_the_database_decides_from_the_name_and_id_alone():
    client = _signing_up()

    _sign_up(client, "u7", "Pat")

    assert client.rpc.calls == [{"p_id": "u7", "p_name": "Pat"}]


def test_the_same_account_signing_up_twice_at_once_is_a_409():
    client = _signing_up()
    _sign_up(client, "u1")

    with pytest.raises(HTTPException) as err:
        _sign_up(client, "u1")  # the profile isn't cached yet: only the database sees the double

    assert err.value.status_code == 409


def test_someone_with_a_profile_cannot_sign_up_again():
    client = _signing_up()
    ctx = _ctx(client=client)

    with pytest.raises(HTTPException) as err:
        invoke(get_registry()["register_profile"], ctx, {"code": get_settings().class_code, "name": "Ana"})

    assert err.value.status_code == 409 and client.rpc.calls == []


def test_a_wrong_code_is_still_refused():
    client = _signing_up()
    ctx = Context(user_id="u1", email="a@b.c", profile=None, client=client)
    with pytest.raises(HTTPException) as err:
        invoke(get_registry()["register_profile"], ctx, {"code": "nope", "name": "Ana"})
    assert err.value.status_code == 403 and client.rpc.calls == []


# -- the approval switch ----------------------------------------------------------------------------


def test_an_admin_turns_approval_on():
    client = _Client(settings=[{"id": 1, "class_language": "en"}])
    ctx = _ctx(role="admin", client=client)

    invoke(get_registry()["update_settings"], ctx, {"signups_need_approval": True})

    assert client.tables["settings"][-1]["signups_need_approval"] is True


def test_approval_is_off_until_turned_on():
    settings = invoke(get_registry()["get_settings"], _ctx(), {})

    assert settings["signups_need_approval"] is False


# -- the cached profile -----------------------------------------------------------------------------


def test_forgetting_a_profile_drops_it_from_the_cache():
    auth._profiles["u9"] = (0.0, {"id": "u9"})

    forget_profile("u9")

    assert "u9" not in auth._profiles


def test_losing_access_forgets_the_profile_and_revokes_the_tokens():
    client = _Client(api_tokens=[
        {"id": 1, "user_id": "u9", "revoked_at": None},
        {"id": 2, "user_id": "u9", "revoked_at": "2026-10-01T00:00:00Z"},
        {"id": 3, "user_id": "u8", "revoked_at": None},
    ])
    auth._profiles["u9"] = (0.0, {"id": "u9"})

    on_access_lost("u9", client)

    assert "u9" not in auth._profiles
    rows = {row["id"]: row for row in client.tables["api_tokens"]}
    assert rows[1]["revoked_at"] and rows[2]["revoked_at"] == "2026-10-01T00:00:00Z"
    assert rows[3]["revoked_at"] is None
