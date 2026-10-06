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


# -- the pages as resources ---------------------------------------------------------------------------


def _with_pages(client):
    client.tables["nodes"] = [
        {"id": 1, "parent_id": None, "kind": "section", "title": "Unit 1", "position": 0, "content_md": ""},
        {"id": 2, "parent_id": 1, "kind": "page", "title": "Loops", "position": 0,
         "content_md": "# Loops\n\nA loop repeats. See [Functions](/node/3). The note said [x](../notes/raw.md).",
         "content_web": "root = Page([])"},
        {"id": 3, "parent_id": 1, "kind": "page", "title": "Functions", "position": 1, "content_md": "Name a block."},
        {"id": 4, "parent_id": 1, "kind": "page", "title": "Empty", "position": 2, "content_md": ""},
    ]
    client.tables["notes"] = [{"id": 9, "user_id": "s1", "status": "pending", "content": "RAW NOTE TEXT"}]


def test_the_shared_pages_are_listed_as_resources(http, client):
    _with_pages(client)

    reply = _rpc(http, _token(client), "resources/list")

    found = {r["uri"]: r for r in reply.json()["result"]["resources"]}
    assert set(found) == {"kolmi://page/2", "kolmi://page/3"}  # a section and an empty page aren't
    assert found["kolmi://page/2"]["name"] == "Loops" and found["kolmi://page/2"]["mimeType"] == "text/markdown"


def test_a_page_reads_as_the_export_writes_it(http, client):
    _with_pages(client)

    reply = _rpc(http, _token(client), "resources/read", {"uri": "kolmi://page/2"})

    text = reply.json()["result"]["contents"][0]["text"]
    assert text.startswith("# Loops\n\nUnit 1\n\nA loop repeats.")
    assert "[Functions](kolmi://page/3)" in text  # another page, as a resource
    assert "../notes/raw.md" not in text and "RAW NOTE TEXT" not in text and "root = Page" not in text


def test_a_page_that_is_not_there_is_a_resource_not_found(http, client):
    _with_pages(client)
    token = _token(client)

    for uri in ("kolmi://page/4", "kolmi://page/99", "kolmi://note/9", "file:///etc/passwd"):
        reply = _rpc(http, token, "resources/read", {"uri": uri})
        assert reply.json()["error"]["code"] == -32002, uri


def test_the_template_names_the_page_uri(http, client):
    reply = _rpc(http, _token(client), "resources/templates/list")

    assert reply.json()["result"]["resourceTemplates"][0]["uriTemplate"] == "kolmi://page/{id}"


def test_no_one_reads_a_page_without_a_good_token(http, client):
    _with_pages(client)
    assert _rpc(http, None, "resources/read", {"uri": "kolmi://page/2"}).status_code == 401
    assert _rpc(http, _token(client, "p1"), "resources/read", {"uri": "kolmi://page/2"}).status_code == 401


# -- the prompt -----------------------------------------------------------------------------------------


def _prompt(http, token, material=None):
    args = {"name": "material_to_notes", **({"arguments": {"material": material}} if material else {})}
    reply = _rpc(http, token, "prompts/get", args)
    return reply.json()["result"]["messages"][0]["content"]["text"]


def test_the_prompt_is_offered(http, client):
    prompts = _rpc(http, _token(client), "prompts/list").json()["result"]["prompts"]

    assert [p["name"] for p in prompts] == ["material_to_notes"]
    assert prompts[0]["arguments"][0]["name"] == "material" and not prompts[0]["arguments"][0]["required"]


def test_a_student_is_guided_to_leave_one_note_per_topic(http, client):
    text = _prompt(http, _token(client), "https://moodle.example/course/7")

    assert "https://moodle.example/course/7" in text
    for step in ("list_nodes", "search_pages", "view_node", "create_note", "source_url", "one note per topic"):
        assert step in text
    assert "write_page" not in text


def test_an_admin_is_guided_to_merge_into_the_page(http, client):
    text = _prompt(http, _token(client, "a1"))

    assert 'write_page in mode "merge"' in text and "create_note" not in text
    assert "what I share or point you to" in text


def test_an_unknown_prompt_is_an_error(http, client):
    reply = _rpc(http, _token(client), "prompts/get", {"name": "nope"})

    assert "error" in reply.json()
