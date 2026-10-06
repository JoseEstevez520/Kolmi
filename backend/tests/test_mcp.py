"""The MCP: personal tokens, who gets in, the tools each role is offered, and the daily cap. The
requests go over HTTP to /mcp, as a client's would."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app import auth, mcp_server, tokens
from app.actions import get_registry, invoke
from app.auth import Context, get_context, on_access_lost

NOW = datetime.now(timezone.utc)


class _Query:
    def __init__(self, table: "_Table", op: str, data: Any = None, count: bool = False, columns: str = "*") -> None:
        self.table, self.op, self.data, self.count = table, op, data, count
        # As PostgREST does, a select answers only the columns asked for.
        self.columns = None if columns.strip() == "*" else [c.strip() for c in columns.split(",")]
        self.tests: list = []

    def eq(self, column, value):
        self.tests.append(lambda row: row.get(column) == value)
        return self

    def is_(self, column, _null):
        self.tests.append(lambda row: row.get(column) is None)
        return self

    def gte(self, column, value):
        self.tests.append(lambda row: str(row.get(column) or "") >= value)
        return self

    def in_(self, column, values):
        self.tests.append(lambda row: row.get(column) in values)
        return self

    def order(self, *_a, **_k):
        return self

    def limit(self, _n):
        return self

    def execute(self):
        rows = self.table.rows
        if self.op == "insert":
            row = {"id": len(rows) + 1, "created_at": NOW.isoformat(), "revoked_at": None, **self.data}
            rows.append(row)
            return SimpleNamespace(data=[row], count=None)
        hits = [row for row in rows if all(test(row) for test in self.tests)]
        if self.op == "update":
            for row in hits:
                row.update(self.data)
        if self.op == "delete":
            self.table.rows[:] = [row for row in rows if row not in hits]
        if self.op == "select" and self.columns:
            hits = [{c: row.get(c) for c in self.columns} for row in hits]
        return SimpleNamespace(data=[dict(row) for row in hits], count=len(hits) if self.count else None)


class _Table:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    def select(self, columns="*", count=None):
        return _Query(self, "select", count=bool(count), columns=columns)

    def update(self, data):
        return _Query(self, "update", data)

    def insert(self, data):
        return _Query(self, "insert", data)

    def delete(self):
        return _Query(self, "delete")

    def upsert(self, data):
        return _Query(self, "insert", data)


class _Client:
    def __init__(self) -> None:
        self.tables: dict[str, list[dict[str, Any]]] = {
            "profiles": [
                {"id": "s1", "name": "Sam", "role": "student", "status": "active"},
                {"id": "a1", "name": "Ana", "role": "admin", "status": "active"},
                {"id": "a2", "name": "Bo", "role": "admin", "status": "active"},
                {"id": "p1", "name": "Pat", "role": "student", "status": "pending"},
            ],
            "api_tokens": [], "notes": [], "settings": [], "files": [],
            "nodes": [{"id": 1, "parent_id": None, "kind": "page", "title": "Loops", "position": 0,
                       "content_md": "A loop repeats.", "content_web": "root = Page([])"}],
        }

    def table(self, name: str) -> _Table:
        return _Table(self.tables.setdefault(name, []))


@pytest.fixture
def client(monkeypatch):
    fake = _Client()
    monkeypatch.setattr(mcp_server, "get_client", lambda: fake)
    auth._profiles.clear()
    yield fake
    auth._profiles.clear()


@pytest.fixture(scope="module")
def http():
    from app.main import app

    with TestClient(app) as http:  # once: the transport's task group runs for the app's life
        yield http


HEADERS = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}


def _rpc(http, token, method, params=None):
    headers = {**HEADERS, **({"Authorization": f"Bearer {token}"} if token else {})}
    body = {"jsonrpc": "2.0", "id": 1, "method": method, **({"params": params} if params else {})}
    return http.post("/mcp", headers=headers, json=body)


def _tools(http, token) -> dict[str, dict]:
    reply = _rpc(http, token, "tools/list")
    assert reply.status_code == 200, reply.text
    return {tool["name"]: tool for tool in reply.json()["result"]["tools"]}


def _call(http, token, name, arguments=None) -> tuple[str, bool]:
    reply = _rpc(http, token, "tools/call", {"name": name, "arguments": arguments or {}})
    assert reply.status_code == 200, reply.text
    result = reply.json()["result"]
    return result["content"][0]["text"], result.get("isError", False)


def _token(client, user_id="s1") -> str:
    return tokens.create(client, user_id, "my editor")["token"]


# -- tokens ---------------------------------------------------------------------------------------


def test_a_token_is_shown_once_and_only_its_hash_is_kept(client):
    made = tokens.create(client, "s1", "laptop")

    assert made["token"].startswith("kolmi_") and len(made["token"]) > 40
    stored = client.tables["api_tokens"][0]
    assert made["token"] not in json.dumps(stored)
    assert stored["prefix"] == made["token"][: tokens.SHOWN]
    assert all("token" not in row and "token_hash" not in row for row in tokens.listed(client, "s1"))


def test_the_token_actions_give_no_token_away(client):
    ctx = Context(user_id="s1", email=None, profile=client.tables["profiles"][0], client=client)
    made = invoke(get_registry()["create_my_token"], ctx, {"name": "laptop"})

    listed = json.dumps(invoke(get_registry()["list_my_tokens"], ctx, {}))

    assert made["token"] not in listed and "token_hash" not in listed


def test_the_token_actions_are_no_tools():
    for name in ("create_my_token", "list_my_tokens", "revoke_my_token"):
        assert not get_registry()[name].tool and not get_registry()[name].mcp


def test_a_member_revokes_only_their_own_tokens(client):
    theirs = tokens.create(client, "a1", "x")
    ctx = Context(user_id="s1", email=None, profile=client.tables["profiles"][0], client=client)

    with pytest.raises(HTTPException) as err:
        invoke(get_registry()["revoke_my_token"], ctx, {"token_id": theirs["id"]})

    assert err.value.status_code == 404 and client.tables["api_tokens"][0]["revoked_at"] is None


def test_the_api_takes_a_token_as_its_owner(client):
    ctx = get_context(authorization=f"Bearer {_token(client)}", client=client)

    assert ctx.user_id == "s1" and ctx.source == "mcp" and ctx.profile["role"] == "student"
    assert client.tables["api_tokens"][0]["last_used_at"]


@pytest.mark.parametrize("bad", ["kolmi_made_up", "kolmi_"])
def test_an_unknown_token_is_a_401(client, bad):
    with pytest.raises(HTTPException) as err:
        get_context(authorization=f"Bearer {bad}", client=client)

    assert err.value.status_code == 401 and bad not in err.value.detail


# -- who gets in through /mcp ----------------------------------------------------------------------


def test_no_token_is_a_401_that_says_it_wants_a_bearer(http, client):
    reply = _rpc(http, None, "tools/list")

    assert reply.status_code == 401 and reply.headers["www-authenticate"].startswith("Bearer")


def test_a_valid_token_gets_in(http, client):
    assert "view_node" in _tools(http, _token(client))


def test_a_revoked_token_is_out(http, client):
    token = _token(client)
    tokens.revoke(client, "s1", client.tables["api_tokens"][0]["id"])

    assert _rpc(http, token, "tools/list").status_code == 401


def test_a_session_token_from_the_app_is_not_taken(http, client):
    assert _rpc(http, "eyJhbGciOi.not.kolmi", "tools/list").status_code == 401


def test_someone_blocked_is_out_at_once(http, client):
    token = _token(client)
    ctx = Context(user_id="a1", email=None, profile=client.tables["profiles"][1], client=client)

    invoke(get_registry()["set_status"], ctx, {"user_id": "s1", "status": "blocked"})

    assert _rpc(http, token, "tools/list").status_code == 401


def test_someone_pending_does_not_get_in(http, client):
    assert _rpc(http, _token(client, "p1"), "tools/list").status_code == 401


def test_an_admin_made_a_student_loses_their_tokens(http, client):
    token = _token(client, "a2")
    assert "write_page_web" in _tools(http, token)
    ctx = Context(user_id="a1", email=None, profile=client.tables["profiles"][1], client=client)

    invoke(get_registry()["set_role"], ctx, {"user_id": "a2", "role": "student"})

    assert _rpc(http, token, "tools/list").status_code == 401


def test_losing_access_revokes_every_token(client):
    for _ in range(2):
        _token(client)

    on_access_lost("s1", client)

    assert all(row["revoked_at"] for row in client.tables["api_tokens"])


# -- the tools each role is offered ------------------------------------------------------------------

STUDENT = {"list_nodes", "view_node", "search_pages", "list_schedule_events", "create_note", "update_note", "my_notes", "delete_note"}
ADMIN_ALSO = {"write_page", "write_page_web", "rebuild_page", "list_versions", "restore_version",
              "list_notes", "view_ai_log", "list_passes", "run_pass"}


def test_a_student_sees_the_student_tools(http, client):
    assert set(_tools(http, _token(client))) == STUDENT


def test_an_admin_sees_the_admin_tools_too(http, client):
    assert set(_tools(http, _token(client, "a1"))) == STUDENT | ADMIN_ALSO


def test_the_hints_follow_the_actions(http, client):
    found = _tools(http, _token(client))

    assert found["view_node"]["annotations"]["readOnlyHint"] is True
    assert found["delete_note"]["annotations"]["destructiveHint"] is True
    assert found["create_note"]["annotations"]["destructiveHint"] is False
    assert found["create_note"]["inputSchema"]["properties"]["source_url"]


@pytest.mark.parametrize(
    "name", sorted(a.name for a in get_registry().values() if not a.mcp)
)
def test_no_ai_can_call_an_action_kept_off_the_mcp(http, client, name):
    text, failed = _call(http, _token(client, "a1"), name, {})

    assert failed and text.startswith(f"There is no tool {name}")


def test_a_student_cannot_call_an_admin_tool(http, client):
    text, failed = _call(http, _token(client), "write_page_web", {"node_id": 1, "content_web": "x"})

    assert failed and text.startswith("There is no tool")
    assert client.tables["nodes"][0]["content_web"] == "root = Page([])"


def test_a_note_through_the_mcp_says_where_it_came_from(http, client):
    _call(http, _token(client), "create_note", {"content": "Loops repeat.", "source_url": "https://moodle/x"})

    note = client.tables["notes"][0]
    assert note["source"] == "mcp" and note["source_url"] == "https://moodle/x" and note["user_id"] == "s1"


def test_an_answer_never_carries_the_token(http, client):
    token = _token(client)

    for name, args in (("view_node", {"node_id": 1}), ("view_node", {"node_id": 99}), ("my_notes", {})):
        text, _ = _call(http, token, name, args)
        assert token not in text


# -- the daily cap -------------------------------------------------------------------------------------


def _cap(client, n):
    client.tables["settings"] = [{"id": 1, "class_language": "en", "mcp_daily_notes": n}]


def test_a_student_s_ai_stops_at_the_daily_cap(http, client):
    _cap(client, 2)
    token = _token(client)

    for i in range(2):
        assert not _call(http, token, "create_note", {"content": f"note {i}"})[1]
    text, failed = _call(http, token, "create_note", {"content": "one too many"})

    assert failed and "Error 429" in text and "2 notes" in text and "midnight" in text
    assert len(client.tables["notes"]) == 2


def test_notes_from_the_app_and_from_yesterday_do_not_count(http, client):
    _cap(client, 1)
    yesterday = (NOW - timedelta(days=2)).isoformat()
    client.tables["notes"] = [
        {"id": 1, "user_id": "s1", "source": "web", "created_at": NOW.isoformat()},
        {"id": 2, "user_id": "s1", "source": "mcp", "created_at": yesterday},
    ]

    assert not _call(http, _token(client), "create_note", {"content": "today's first"})[1]


def test_an_admin_has_no_cap(http, client):
    _cap(client, 1)
    token = _token(client, "a1")

    for i in range(3):
        assert not _call(http, token, "create_note", {"content": f"note {i}"})[1]


# -- search and one's own notes ---------------------------------------------------------------------


def test_search_finds_a_page_by_its_text(http, client):
    text, failed = _call(http, _token(client), "search_pages", {"query": "loop repeats"})

    assert not failed and json.loads(text)[0]["id"] == 1


def test_a_student_deletes_their_own_pending_note(http, client):
    client.tables["notes"] = [{"id": 5, "user_id": "s1", "status": "pending", "content": "x"}]

    text, failed = _call(http, _token(client), "delete_note", {"note_id": 5})

    assert not failed and client.tables["notes"] == []


def test_someone_else_s_note_stays(http, client):
    client.tables["notes"] = [{"id": 5, "user_id": "a1", "status": "pending", "content": "x"}]

    text, failed = _call(http, _token(client), "delete_note", {"note_id": 5})

    assert failed and len(client.tables["notes"]) == 1


# -- a token reaches only the MCP's tools, through any route ----------------------------------------


@pytest.mark.parametrize(
    "name,args",
    [
        ("list_users", {}),
        ("delete_user", {"user_id": "s1"}),
        ("update_settings", {"mcp_daily_notes": 999}),
        ("create_my_token", {"name": "another"}),
        ("revoke_my_token", {"token_id": 1}),
        ("delete_my_account", {}),
        ("create_node", {"kind": "page", "title": "x"}),
    ],
)
def test_a_token_cannot_reach_what_is_kept_off_the_mcp(client, name, args):
    ctx = get_context(authorization=f"Bearer {_token(client, 'a1')}", client=client)

    with pytest.raises(HTTPException) as err:
        invoke(get_registry()[name], ctx, args)

    assert err.value.status_code == 403 and "in the app" in err.value.detail
    assert len(client.tables["api_tokens"]) == 1 and client.tables["profiles"][0]["id"] == "s1"


def test_a_token_cannot_upload_or_export(client):
    from app.export_api import export
    from app.files_api import store_upload

    ctx = get_context(authorization=f"Bearer {_token(client)}", client=client)
    for attempt in (
        lambda: store_upload(ctx, name="a.pdf", mime="application/pdf", data=b"%PDF", note_id=1),
        lambda: export(None, ctx),
    ):
        with pytest.raises(HTTPException) as err:
            attempt()
        assert err.value.status_code == 403
