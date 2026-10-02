from __future__ import annotations

from typing import Any

import pytest
from fastapi import HTTPException

from app import auth


class _Auth:
    def __init__(self, claims: dict[str, Any] | None, error: Exception | None = None) -> None:
        self.claims = claims
        self.error = error

    def get_claims(self, token: str) -> dict[str, Any] | None:
        if self.error:
            raise self.error
        return {"claims": self.claims, "headers": {}, "signature": b""} if self.claims else None


class _Profiles:
    """The profiles table, counting how often it is read."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self.reads = 0
        self._id = None

    def select(self, _columns: str) -> _Profiles:
        return self

    def eq(self, _column: str, value: Any) -> _Profiles:
        self._id = value
        return self

    def limit(self, _n: int) -> _Profiles:
        return self

    def execute(self) -> Any:
        self.reads += 1
        data = [r for r in self.rows if r["id"] == self._id]
        return type("Response", (), {"data": data})()


class _Client:
    def __init__(self, claims, rows=(), error=None) -> None:
        self.auth = _Auth(claims, error)
        self.profiles = _Profiles(list(rows))

    def table(self, name: str) -> _Profiles:
        assert name == "profiles"
        return self.profiles


@pytest.fixture(autouse=True)
def _fresh_cache():
    auth._profiles.clear()
    yield
    auth._profiles.clear()


def test_a_valid_token_gives_the_user_and_profile():
    client = _Client({"sub": "u1", "email": "a@b.c"}, [{"id": "u1", "role": "admin"}])
    ctx = auth.get_context("Bearer t", client)
    assert ctx.user_id == "u1"
    assert ctx.email == "a@b.c"
    assert ctx.profile["role"] == "admin"


def test_a_bad_token_is_refused():
    client = _Client(None, error=ValueError("Invalid JWT signature"))
    with pytest.raises(HTTPException) as error:
        auth.get_context("Bearer forged", client)
    assert error.value.status_code == 401


def test_a_token_without_a_user_is_refused():
    client = _Client({"role": "anon"})
    with pytest.raises(HTTPException) as error:
        auth.get_context("Bearer anon", client)
    assert error.value.status_code == 401


def test_the_profile_is_read_once_for_a_few_requests():
    client = _Client({"sub": "u1"}, [{"id": "u1"}])
    for _ in range(3):
        auth.get_context("Bearer t", client)
    assert client.profiles.reads == 1


def test_a_missing_profile_is_not_kept():
    client = _Client({"sub": "u1"})
    assert auth.get_context("Bearer t", client).profile is None
    # The user registers: the next request sees the profile.
    client.profiles.rows.append({"id": "u1"})
    assert auth.get_context("Bearer t", client).profile == {"id": "u1"}


def test_a_profile_is_read_again_after_a_while(monkeypatch):
    client = _Client({"sub": "u1"}, [{"id": "u1"}])
    now = [1000.0]
    monkeypatch.setattr(auth.time, "monotonic", lambda: now[0])
    auth.get_context("Bearer t", client)
    now[0] += auth.PROFILE_TTL + 1
    auth.get_context("Bearer t", client)
    assert client.profiles.reads == 2
