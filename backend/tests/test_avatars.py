from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.actions.live_notes import _followers
from app.actions.profile import get_profile
from app.auth import Context
from app.avatar_api import clear_avatar, set_avatar
from app.avatars import MAX_AVATAR_BYTES, avatar_url

JPEG = b"\xff\xd8\xff\xe0" + b"0" * 20
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 20
WEBP = b"RIFF\x10\x00\x00\x00WEBPVP8 "


class _Query:
    def __init__(self, rows, op, data=None):
        self.rows, self.op, self.data, self.filters = rows, op, data, []

    def eq(self, column, value):
        self.filters.append((column, value))
        return self

    def in_(self, column, values):
        self.filters.append((column, values))
        return self

    def limit(self, _n):
        return self

    def execute(self):
        hit = [r for r in self.rows if all(r.get(c) == v or (isinstance(v, list) and r.get(c) in v) for c, v in self.filters)]
        if self.op == "update":
            for r in hit:
                r.update(self.data)
        return type("Response", (), {"data": [dict(r) for r in hit]})()


class _Table:
    def __init__(self, rows):
        self.rows = rows

    def select(self, _c):
        return _Query(self.rows, "select")

    def update(self, data):
        return _Query(self.rows, "update", data)


class _Bucket:
    def __init__(self):
        self.objects = {}

    def upload(self, path, data, options=None):
        self.objects[path] = (data, options)

    def remove(self, paths):
        for path in paths:
            self.objects.pop(path, None)


class _Client:
    def __init__(self):
        self.profiles = [
            {"id": "u1", "name": "Ana", "status": "active", "avatar_path": None},
            {"id": "u2", "name": "Bo", "status": "active", "avatar_path": "bo.jpg"},
        ]
        self.bucket = _Bucket()
        self.bucket.objects["bo.jpg"] = (b"x", None)
        self.storage = type("Storage", (), {"from_": lambda _s, _n: self.bucket})()

    def table(self, name):
        assert name == "profiles"
        return _Table(self.profiles)


def ctx(client, user="u1", status="active", source="web"):
    profile = next(p for p in client.profiles if p["id"] == user) | {"status": status}
    return Context(user_id=user, email=None, profile=profile, client=client, source=source)


def test_a_photo_is_stored_and_linked():
    client = _Client()
    out = set_avatar(ctx(client), JPEG)
    (path,) = [p for p in client.bucket.objects if p != "bo.jpg"]
    assert path.endswith(".jpg") and len(path) == 36
    assert client.profiles[0]["avatar_path"] == path
    assert out == {"avatar_url": avatar_url(path)}
    assert out["avatar_url"].endswith(f"/storage/v1/object/public/avatars/{path}")


@pytest.mark.parametrize("data", [PNG, WEBP])
def test_png_and_webp_pass(data):
    set_avatar(ctx(_Client()), data)


@pytest.mark.parametrize("data", [b"GIF89a....", b"<svg></svg>", b"RIFF\x00\x00\x00\x00WAVE", b"hello"])
def test_other_bytes_are_refused_whatever_the_name(data):
    client = _Client()
    with pytest.raises(HTTPException) as error:
        set_avatar(ctx(client), data)
    assert error.value.status_code == 415
    assert len(client.bucket.objects) == 1


def test_too_big_or_empty_is_refused():
    client = _Client()
    with pytest.raises(HTTPException) as error:
        set_avatar(ctx(client), JPEG + b"0" * MAX_AVATAR_BYTES)
    assert error.value.status_code == 413
    with pytest.raises(HTTPException):
        set_avatar(ctx(client), b"")
    set_avatar(ctx(client), JPEG + b"0" * (MAX_AVATAR_BYTES - len(JPEG)))


def test_only_active_members_in_the_app():
    client = _Client()
    with pytest.raises(HTTPException) as error:
        set_avatar(ctx(client, status="pending"), JPEG)
    assert error.value.status_code == 403
    with pytest.raises(HTTPException):
        set_avatar(ctx(client, source="mcp"), JPEG)
    with pytest.raises(HTTPException):
        clear_avatar(ctx(client, status="blocked"))


def test_it_only_touches_your_own():
    client = _Client()
    set_avatar(ctx(client, "u1"), JPEG)
    assert client.profiles[1]["avatar_path"] == "bo.jpg"
    assert "bo.jpg" in client.bucket.objects


def test_replacing_deletes_the_old_object():
    client = _Client()
    first = set_avatar(ctx(client, "u2"), PNG)["avatar_url"].rsplit("/", 1)[1]
    assert "bo.jpg" not in client.bucket.objects
    second = set_avatar(ctx(client, "u2"), JPEG)["avatar_url"].rsplit("/", 1)[1]
    assert first not in client.bucket.objects and second in client.bucket.objects
    assert client.profiles[1]["avatar_path"] == second


def test_removing_nulls_the_column_and_the_object():
    client = _Client()
    assert clear_avatar(ctx(client, "u2")) == {"avatar_url": None}
    assert client.profiles[1]["avatar_path"] is None
    assert "bo.jpg" not in client.bucket.objects
    assert clear_avatar(ctx(client, "u2")) == {"avatar_url": None}


def test_a_failed_removal_does_not_fail_the_request():
    client = _Client()
    client.bucket.remove = lambda _p: (_ for _ in ()).throw(RuntimeError("storage down"))
    assert clear_avatar(ctx(client, "u2")) == {"avatar_url": None}
    assert client.profiles[1]["avatar_path"] is None


def test_followers_and_the_profile_carry_the_link():
    client = _Client()
    out = _followers(ctx(client), ["u1", "u2"])["followers"]
    assert out[0] == {"id": "u1", "name": "Ana", "avatar_url": None}
    assert out[1]["avatar_url"] == avatar_url("bo.jpg")
    mine = get_profile(ctx(client, "u2"), None)
    assert mine["avatar_url"] == avatar_url("bo.jpg") and "avatar_path" not in mine
