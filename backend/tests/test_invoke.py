from __future__ import annotations

from typing import Any

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.actions import Action, get_registry, has_role, invoke
from app.auth import Context, get_context
from app.main import app


class _Untouched:
    """A client that fails the test if anything reaches the database."""

    def table(self, _name: str) -> Any:
        raise AssertionError("touched the database")

    @property
    def storage(self) -> Any:
        raise AssertionError("touched the database")


def _ctx(role: str = "student", approved: bool = True, profile: bool = True) -> Context:
    data = {"id": "u1", "name": "Ana", "role": role, "approved": approved} if profile else None
    return Context(user_id="u1", email=None, profile=data, client=_Untouched())


class _Params(BaseModel):
    count: int = 1
    label: str = "x"


def _echo(_ctx: Context, params: _Params | None):
    return params.model_dump() if params else None


_ADMIN = Action(name="admin_thing", description="d", handler=_echo, params=_Params, min_role="admin")
_OPEN = Action(name="open_thing", description="d", handler=_echo, params=_Params)


@pytest.mark.parametrize(
    "name, args",
    [
        ("delete_node", {"node_id": 1}),
        ("create_node", {"kind": "page", "title": "T"}),
        ("run_pass", {}),
        ("update_settings", {"class_language": "es"}),
    ],
)
def test_a_student_cannot_run_an_admin_action(name, args):
    with pytest.raises(HTTPException) as exc:
        invoke(get_registry()[name], _ctx(), args)

    assert exc.value.status_code == 403


def test_an_admin_runs_an_admin_action():
    assert invoke(_ADMIN, _ctx("admin"), {"count": 3}) == {"count": 3, "label": "x"}


def test_no_profile_counts_as_a_student():
    assert not has_role(_ctx(profile=False), "admin")
    assert has_role(_ctx(profile=False), "student")
    with pytest.raises(HTTPException) as exc:
        invoke(_ADMIN, _ctx(profile=False), {})
    assert exc.value.status_code == 403


def test_bad_params_are_a_422_naming_the_field():
    with pytest.raises(HTTPException) as exc:
        invoke(_OPEN, _ctx(), {"count": "many"})

    assert exc.value.status_code == 422
    assert "count" in exc.value.detail


def test_the_role_is_checked_before_the_params():
    with pytest.raises(HTTPException) as exc:
        invoke(_ADMIN, _ctx(), {"count": "many"})

    assert exc.value.status_code == 403


def test_no_args_means_the_defaults():
    assert invoke(_OPEN, _ctx(), None) == {"count": 1, "label": "x"}


def test_an_unapproved_profile_cannot_create_a_note():
    with pytest.raises(HTTPException) as exc:
        invoke(get_registry()["create_note"], _ctx(approved=False), {"content": "hi"})

    assert exc.value.status_code == 403


def test_the_routes_go_through_invoke():
    client = TestClient(app)
    app.dependency_overrides[get_context] = lambda: _ctx()
    try:
        assert client.post("/node/delete", json={"node_id": 1}).status_code == 403
        response = client.get("/node", params={"node_id": "abc"})
        assert response.status_code == 422
        assert isinstance(response.json()["detail"], str)
    finally:
        app.dependency_overrides.clear()
