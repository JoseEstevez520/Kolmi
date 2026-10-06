"""The class's people: listing them, roles, status, the last admin, and deleting an account."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException

from app import auth
from app.actions import get_registry, invoke
from app.auth import Context
from tests.test_content import _Table


class _Bucket:
    def __init__(self, fail: bool = False) -> None:
        self.removed: list[list[str]] = []
        self.fail = fail

    def remove(self, paths: list[str]) -> None:
        if self.fail:
            raise RuntimeError("storage is down")
        self.removed.append(list(paths))


class _Admin:
    def __init__(self, emails: dict[str, str], fail: bool = False) -> None:
        self.emails = emails
        self.deleted: list[str] = []
        self.fail = fail

    def list_users(self, page=None, per_page=None):
        if self.fail:
            raise RuntimeError("auth is down")
        return [SimpleNamespace(id=uid, email=email) for uid, email in self.emails.items()]

    def delete_user(self, user_id: str) -> None:
        if self.fail:
            raise RuntimeError("auth is down")
        self.deleted.append(user_id)


class _Client:
    def __init__(self, profiles, notes=(), files=(), bucket=None, admin=None) -> None:
        self.tables: dict[str, list[dict[str, Any]]] = {
            "profiles": list(profiles), "notes": list(notes), "files": list(files),
        }
        self.bucket = bucket or _Bucket()
        self.storage = SimpleNamespace(from_=lambda _name: self.bucket)
        self.auth = SimpleNamespace(admin=admin or _Admin({"a1": "ana@class.org", "s1": "sam@class.org"}))

    def table(self, name: str) -> _Table:
        return _Table(self.tables.setdefault(name, []))


def _people(**extra):
    return [
        {"id": "a1", "name": "Ana", "role": "admin", "status": "active", "created_at": "2026-10-01"},
        {"id": "s1", "name": "Sam", "role": "student", "status": "active", "created_at": "2026-10-02"},
        {"id": "p1", "name": "Pat", "role": "student", "status": "pending", "created_at": "2026-10-03"},
        *extra.get("more", []),
    ]


def _ctx(client, user="a1", role="admin", status="active") -> Context:
    profile = {"id": user, "name": "Me", "role": role, "status": status}
    return Context(user_id=user, email=None, profile=profile, client=client)


def _run(client, name, args=None, **who):
    return invoke(get_registry()[name], _ctx(client, **who), args or {})


def _error(client, name, args=None, **who) -> HTTPException:
    with pytest.raises(HTTPException) as err:
        _run(client, name, args, **who)
    return err.value


def _row(client, user_id):
    return next(p for p in client.tables["profiles"] if p["id"] == user_id)


# -- listing --------------------------------------------------------------------------------------


def test_an_admin_lists_the_class_with_emails_and_note_counts():
    client = _Client(_people(), notes=[{"id": 1, "user_id": "s1"}, {"id": 2, "user_id": "s1"}])

    people = {p["id"]: p for p in _run(client, "list_users")}

    assert people["s1"]["email"] == "sam@class.org" and people["s1"]["notes"] == 2
    assert people["p1"]["status"] == "pending" and people["p1"]["email"] is None
    assert people["a1"]["notes"] == 0


def test_the_list_still_shows_when_emails_cannot_be_read():
    client = _Client(_people(), admin=_Admin({}, fail=True))

    assert all(p["email"] is None for p in _run(client, "list_users"))


def test_a_student_cannot_list_the_class():
    assert _error(_Client(_people()), "list_users", user="s1", role="student").status_code == 403


@pytest.mark.parametrize(
    "name,args",
    [
        ("set_role", {"user_id": "s1", "role": "admin"}),
        ("set_status", {"user_id": "s1", "status": "blocked"}),
        ("delete_user", {"user_id": "s1"}),
    ],
)
def test_a_student_cannot_manage_people(name, args):
    client = _Client(_people())

    assert _error(client, name, args, user="s1", role="student").status_code == 403
    assert _row(client, "s1")["status"] == "active" and client.auth.admin.deleted == []


def test_managing_people_is_never_over_the_mcp():
    for name in ("list_users", "set_role", "set_status", "delete_user", "update_my_name", "delete_my_account"):
        assert not get_registry()[name].mcp


# -- roles and status -----------------------------------------------------------------------------


def test_an_admin_makes_someone_an_admin():
    client = _Client(_people())

    _run(client, "set_role", {"user_id": "s1", "role": "admin"})

    assert _row(client, "s1")["role"] == "admin"


def test_an_admin_lets_a_pending_sign_up_in():
    client = _Client(_people())

    _run(client, "set_status", {"user_id": "p1", "status": "active"})

    assert _row(client, "p1")["status"] == "active"


def test_demoting_or_blocking_forgets_their_cached_profile():
    client = _Client(_people(more=[{"id": "a2", "name": "Bo", "role": "admin", "status": "active"}]))
    auth._profiles["a2"] = (0.0, {"id": "a2"})
    auth._profiles["s1"] = (0.0, {"id": "s1"})

    _run(client, "set_role", {"user_id": "a2", "role": "student"})
    _run(client, "set_status", {"user_id": "s1", "status": "blocked"})

    assert "a2" not in auth._profiles and "s1" not in auth._profiles
    assert _row(client, "a2")["role"] == "student" and _row(client, "s1")["status"] == "blocked"


def test_someone_missing_is_a_404_that_says_where_to_look():
    err = _error(_Client(_people()), "set_status", {"user_id": "nobody", "status": "active"})

    assert err.status_code == 404 and "list_users" in err.detail


def test_a_wrong_role_or_status_is_a_422():
    assert _error(_Client(_people()), "set_role", {"user_id": "s1", "role": "teacher"}).status_code == 422
    assert _error(_Client(_people()), "set_status", {"user_id": "s1", "status": "gone"}).status_code == 422


# -- the last admin -------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name,args",
    [
        ("set_role", {"user_id": "a1", "role": "student"}),
        ("set_status", {"user_id": "a1", "status": "blocked"}),
        ("set_status", {"user_id": "a1", "status": "pending"}),
        ("delete_user", {"user_id": "a1"}),
    ],
)
def test_the_last_admin_stays(name, args):
    client = _Client(_people())

    err = _error(client, name, args)

    assert err.status_code == 409 and "last admin" in err.detail and "make someone else an admin" in err.detail
    assert _row(client, "a1")["role"] == "admin" and _row(client, "a1")["status"] == "active"
    assert client.auth.admin.deleted == []


def test_a_blocked_admin_does_not_count_as_the_one_that_stays():
    client = _Client(_people(more=[{"id": "a2", "name": "Bo", "role": "admin", "status": "blocked"}]))

    assert _error(client, "set_role", {"user_id": "a1", "role": "student"}).status_code == 409


def test_with_two_admins_one_can_step_down():
    client = _Client(_people(more=[{"id": "a2", "name": "Bo", "role": "admin", "status": "active"}]))

    _run(client, "set_role", {"user_id": "a1", "role": "student"})

    assert _row(client, "a1")["role"] == "student"


def test_the_last_admin_cannot_delete_their_own_account():
    client = _Client(_people())

    err = _error(client, "delete_my_account")

    assert err.status_code == 409 and err.detail.startswith("You're the class's last admin")


# -- deleting an account --------------------------------------------------------------------------


def _with_files():
    notes = [{"id": 1, "user_id": "s1", "status": "pending"}, {"id": 2, "user_id": "s1", "status": "processed"},
             {"id": 3, "user_id": "a1", "status": "pending"}]
    files = [
        {"id": 10, "note_id": 1, "node_id": None, "user_id": "s1", "path": "notes/1/a.pdf"},
        {"id": 11, "note_id": None, "node_id": 7, "user_id": "s1", "path": "pages/7/b.pdf"},
        {"id": 12, "note_id": 3, "node_id": None, "user_id": "a1", "path": "notes/3/c.pdf"},
    ]
    return _Client(_people(), notes=notes, files=files)


def test_deleting_someone_takes_their_notes_files_and_the_account():
    client = _with_files()
    auth._profiles["s1"] = (0.0, {"id": "s1"})

    assert _run(client, "delete_user", {"user_id": "s1"}) == {"deleted": "s1"}

    assert client.bucket.removed == [["notes/1/a.pdf"]]  # not the shared page's, not anyone else's
    assert client.auth.admin.deleted == ["s1"]
    assert "s1" not in auth._profiles


def test_storage_failing_deletes_nothing():
    client = _with_files()
    client.bucket.fail = True

    err = _error(client, "delete_user", {"user_id": "s1"})

    assert err.status_code == 502 and "nothing was deleted" in err.detail
    assert client.auth.admin.deleted == []


def test_auth_failing_says_to_try_again():
    client = _with_files()
    client.auth.admin.fail = True

    err = _error(client, "delete_user", {"user_id": "s1"})

    assert err.status_code == 502 and "try again" in err.detail


def test_a_member_deletes_their_own_account():
    client = _with_files()

    _run(client, "delete_my_account", user="s1", role="student")

    assert client.auth.admin.deleted == ["s1"] and client.bucket.removed == [["notes/1/a.pdf"]]


@pytest.mark.parametrize("status", ["pending", "blocked"])
def test_someone_not_let_in_can_still_delete_their_account(status):
    client = _Client(_people())

    _run(client, "delete_my_account", user="p1", role="student", status=status)

    assert client.auth.admin.deleted == ["p1"]


def test_many_files_go_in_batches():
    notes = [{"id": n, "user_id": "s1"} for n in range(1, 251)]
    files = [{"id": n, "note_id": n, "node_id": None, "user_id": "s1", "path": f"notes/{n}/f"} for n in range(1, 251)]
    client = _Client(_people(), notes=notes, files=files)

    _run(client, "delete_user", {"user_id": "s1"})

    assert [len(batch) for batch in client.bucket.removed] == [100, 100, 50]


# -- one's own name --------------------------------------------------------------------------------


def test_a_member_changes_their_name():
    client = _Client(_people())
    auth._profiles["s1"] = (0.0, {"id": "s1"})

    row = _run(client, "update_my_name", {"name": "  Samuel  "}, user="s1", role="student")

    assert row["name"] == "Samuel" and _row(client, "s1")["name"] == "Samuel"
    assert "s1" not in auth._profiles


def test_a_blank_name_is_refused():
    assert _error(_Client(_people()), "update_my_name", {"name": "   "}, user="s1", role="student").status_code == 422


def test_someone_pending_cannot_change_their_name():
    client = _Client(_people())

    assert _error(client, "update_my_name", {"name": "X"}, user="p1", role="student", status="pending").status_code == 403
