"""Who may do anything at all: the status checked once in invoke, sign-up, and the cached profile."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi import HTTPException

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


@pytest.fixture
def admin_emails(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "admin_emails", "First@Class.org, other@class.org")
    return settings


def _sign_up(client, email="ana@class.org"):
    ctx = Context(user_id="u1", email=email, profile=None, client=client)
    return invoke(get_registry()["register_profile"], ctx, {"code": get_settings().class_code, "name": "Ana"})


def test_an_address_in_admin_emails_signs_up_as_an_active_admin(admin_emails):
    client = _Client(settings=[{"id": 1, "class_language": "en", "signups_need_approval": True}])

    row = _sign_up(client, "first@class.org")

    assert row["role"] == "admin" and row["status"] == "active"


def test_anyone_else_signs_up_as_an_active_student(admin_emails):
    row = _sign_up(_Client())

    assert row["role"] == "student" and row["status"] == "active"


def test_with_approval_on_a_new_sign_up_waits(admin_emails):
    client = _Client(settings=[{"id": 1, "class_language": "en", "signups_need_approval": True}])

    row = _sign_up(client)

    assert row["role"] == "student" and row["status"] == "pending"


def test_a_wrong_code_is_still_refused():
    ctx = Context(user_id="u1", email="a@b.c", profile=None, client=_Client())
    with pytest.raises(HTTPException) as err:
        invoke(get_registry()["register_profile"], ctx, {"code": "nope", "name": "Ana"})
    assert err.value.status_code == 403


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


def test_losing_access_forgets_the_profile():
    auth._profiles["u9"] = (0.0, {"id": "u9"})

    on_access_lost("u9")

    assert "u9" not in auth._profiles
