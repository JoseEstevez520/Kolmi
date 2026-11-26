"""MCP OAuth 2.1 support: protected-resource metadata (RFC 9728), WWW-Authenticate challenge,
and accepting Supabase JWT access tokens alongside `kolmi_...` tokens when MCP_OAUTH_ENABLED is on."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app import auth, mcp_server, tokens
from app.actions import get_registry, invoke
from app.auth import Context
from app.config import Settings

NOW = datetime.now(timezone.utc)


class _Query:
    def __init__(self, table: "_Table", op: str, data: Any = None, count: bool = False, columns: str = "*") -> None:
        self.table, self.op, self.data, self.count = table, op, data, count
        self.columns = None if columns.strip() == "*" else [c.strip() for c in columns.split(",")]
        self.tests: list = []

    def eq(self, column, value):
        self.tests.append(lambda row: row.get(column) == value)
        return self

    def is_(self, column, _null):
        self.tests.append(lambda row: row.get(column) is None)
        return self

    def gte(self, column, value):
        self.tests.append(lambda row: str(row.get(column) or "") >= str(value))
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


class _Auth:
    def __init__(self) -> None:
        self.jwts: dict[str, dict[str, Any] | Exception] = {}

    def get_claims(self, token: str) -> dict[str, Any] | None:
        entry = self.jwts.get(token)
        if isinstance(entry, Exception):
            raise entry
        if entry is None:
            raise ValueError("Invalid JWT")
        return {"claims": entry, "headers": {}, "signature": b""}


class _Client:
    def __init__(self) -> None:
        self.auth = _Auth()
        self.tables: dict[str, list[dict[str, Any]]] = {
            "profiles": [
                {"id": "s1", "name": "Sam", "role": "student", "status": "active"},
                {"id": "a1", "name": "Ana", "role": "admin", "status": "active"},
                {"id": "a2", "name": "Bo", "role": "admin", "status": "active"},
                {"id": "b1", "name": "Ban", "role": "student", "status": "blocked"},
                {"id": "p1", "name": "Pat", "role": "student", "status": "pending"},
            ],
            "api_tokens": [],
            "notes": [],
            "settings": [],
            "files": [],
            "nodes": [
                {
                    "id": 1,
                    "parent_id": None,
                    "kind": "page",
                    "title": "Loops",
                    "position": 0,
                    "content_md": "A loop repeats.",
                    "content_web": "root = Page([])",
                }
            ],
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
    from contextlib import asynccontextmanager
    from starlette.applications import Starlette
    manager = mcp_server.StreamableHTTPSessionManager(
        app=mcp_server.server, json_response=True, stateless=True,
        security_settings=mcp_server.TransportSecuritySettings(enable_dns_rebinding_protection=False),
    )
    @asynccontextmanager
    async def lifespan(app):
        async with manager.run():
            yield
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(mcp_server, "sessions", manager)
        app = Starlette(routes=[*mcp_server.metadata_routes(), mcp_server.route()], lifespan=lifespan)
        with TestClient(app) as http:
            yield http


def _settings(monkeypatch, *, enabled: bool, public_url: str = "", supabase_url: str = "https://proj.supabase.co"):
    cfg = Settings(
        supabase_url=supabase_url,
        supabase_service_key="test",
        class_code="test",
        mcp_oauth_enabled=enabled,
        public_url=public_url or "http://testserver",
    )
    monkeypatch.setattr(mcp_server, "get_settings", lambda: cfg)


HEADERS = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}


def _rpc(http, token: str | None, method: str, params: dict | None = None):
    headers = {**HEADERS, **({"Authorization": f"Bearer {token}"} if token else {})}
    body = {"jsonrpc": "2.0", "id": 1, "method": method, **({"params": params} if params else {})}
    return http.post("/mcp", headers=headers, json=body)


def _tools(http, token: str) -> set[str]:
    reply = _rpc(http, token, "tools/list")
    assert reply.status_code == 200, reply.text
    return {t["name"] for t in reply.json()["result"]["tools"]}


# -- flag off (default) ---------------------------------------------------------------------------


def test_flag_off_hides_metadata_omits_resource_metadata_and_refuses_jwts(http, client, monkeypatch):
    _settings(monkeypatch, enabled=False)
    client.auth.jwts["jwt-student"] = {"sub": "s1", "exp": int(time.time()) + 3600}
    personal = tokens.create(client, "s1", "cli")["token"]

    assert http.get("/.well-known/oauth-protected-resource").status_code == 404
    assert http.get("/.well-known/oauth-protected-resource/mcp").status_code == 404

    unauth = _rpc(http, None, "tools/list")
    assert unauth.status_code == 401
    assert "resource_metadata" not in unauth.headers["www-authenticate"]

    assert _rpc(http, "jwt-student", "tools/list").status_code == 401
    assert "view_node" in _tools(http, personal)


# -- flag on: metadata and 401 challenge ----------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    ["/.well-known/oauth-protected-resource", "/.well-known/oauth-protected-resource/mcp"],
)
def test_protected_resource_metadata_uses_request_origin_or_public_url(http, client, monkeypatch, path):
    _settings(monkeypatch, enabled=True, supabase_url="https://abc.supabase.co/")
    reply = http.get(path)
    assert reply.status_code == 200
    assert reply.json() == {
        "resource": "http://testserver/mcp",
        "authorization_servers": ["https://abc.supabase.co/auth/v1"],
        "bearer_methods_supported": ["header"],
    }

    _settings(
        monkeypatch,
        enabled=True,
        public_url="https://daw2.kolmi.es/",
        supabase_url="https://abc.supabase.co",
    )
    reply_pub = http.get(path)
    assert reply_pub.status_code == 200
    assert reply_pub.json() == {
        "resource": "https://daw2.kolmi.es/mcp",
        "authorization_servers": ["https://abc.supabase.co/auth/v1"],
        "bearer_methods_supported": ["header"],
    }


def test_unauthenticated_mcp_challenge_points_to_resource_metadata(http, client, monkeypatch):
    _settings(monkeypatch, enabled=True)
    reply = _rpc(http, None, "tools/list")

    assert reply.status_code == 401
    header = reply.headers["www-authenticate"]
    assert header.startswith("Bearer ")
    assert 'resource_metadata="http://testserver/.well-known/oauth-protected-resource/mcp"' in header

    _settings(monkeypatch, enabled=True, public_url="https://daw2.kolmi.es")
    reply_pub = _rpc(http, None, "tools/list")
    assert (
        'resource_metadata="https://daw2.kolmi.es/.well-known/oauth-protected-resource/mcp"'
        in reply_pub.headers["www-authenticate"]
    )


# -- flag on: personal tokens and OAuth JWTs ------------------------------------------------------


def test_both_personal_tokens_and_valid_jwts_work_when_enabled(http, client, monkeypatch):
    _settings(monkeypatch, enabled=True)
    personal = tokens.create(client, "s1", "cli")["token"]
    client.auth.jwts["jwt-student"] = {
        "sub": "s1",
        "email": "sam@example.com",
        "scope": "openid email",
        "client_id": "chatgpt-connector",
        "exp": int(time.time()) + 3600,
    }
    client.auth.jwts["jwt-admin"] = {
        "sub": "a1",
        "scope": "openid",
        "exp": int(time.time()) + 3600,
    }

    for key in ("jwt-student", "jwt-admin"):
        client.auth.jwts[key].update(aud="http://testserver/mcp", iss="https://proj.supabase.co/auth/v1", client_id="connector")
    student_tools = _tools(http, "jwt-student")
    assert student_tools == _tools(http, personal)
    assert "create_note" in student_tools and "write_page" not in student_tools
    assert "write_page" in _tools(http, "jwt-admin")

    created = _rpc(
        http,
        "jwt-student",
        "tools/call",
        {"name": "create_note", "arguments": {"content": "From OAuth chat"}},
    )
    assert created.status_code == 200 and not created.json()["result"].get("isError")
    assert client.tables["notes"][0]["user_id"] == "s1"
    assert client.tables["notes"][0]["source"] == "mcp"


def test_invalid_or_expired_jwts_are_refused(http, client, monkeypatch):
    _settings(monkeypatch, enabled=True)
    client.auth.jwts["jwt-expired"] = {"sub": "s1", "exp": int(time.time()) - 10}
    client.auth.jwts["jwt-anon"] = {"role": "anon", "exp": int(time.time()) + 3600}
    client.auth.jwts["jwt-forged"] = ValueError("Invalid signature")

    for bad in ("jwt-expired", "jwt-anon", "jwt-forged", "jwt-unknown"):
        reply = _rpc(http, bad, "tools/list")
        assert reply.status_code == 401, bad


def test_blocked_pending_or_unregistered_jwt_is_refused(http, client, monkeypatch):
    _settings(monkeypatch, enabled=True)
    now = int(time.time()) + 3600
    client.auth.jwts["jwt-blocked"] = {"sub": "b1", "exp": now}
    client.auth.jwts["jwt-pending"] = {"sub": "p1", "exp": now}
    client.auth.jwts["jwt-no-profile"] = {"sub": "ghost", "exp": now}
    client.auth.jwts["jwt-active"] = {"sub": "s1", "exp": now}

    for denied in ("jwt-blocked", "jwt-pending", "jwt-no-profile"):
        assert _rpc(http, denied, "tools/list").status_code == 401, denied

    client.auth.jwts["jwt-active"].update(aud="http://testserver/mcp", iss="https://proj.supabase.co/auth/v1", client_id="connector")
    # Active first, then blocked by an admin: cut off on the next request.
    assert "view_node" in _tools(http, "jwt-active")
    admin_ctx = Context(user_id="a1", email=None, profile=client.tables["profiles"][1], client=client)
    invoke(get_registry()["set_status"], admin_ctx, {"user_id": "s1", "status": "blocked"})
    assert _rpc(http, "jwt-active", "tools/list").status_code == 401


def test_oauth_rejects_wrong_resource_issuer_or_missing_client(http, client, monkeypatch):
    _settings(monkeypatch, enabled=True)
    good = dict(sub="s1", exp=int(time.time()) + 300, aud="http://testserver/mcp", iss="https://proj.supabase.co/auth/v1", client_id="connector")
    for change in ({"aud": "authenticated"}, {"iss": "https://other.example/auth/v1"}, {"client_id": ""}, {"exp": None}):
        client.auth.jwts["invalid-target"] = {**good, **change}
        assert _rpc(http, "invalid-target", "tools/list").status_code == 401
