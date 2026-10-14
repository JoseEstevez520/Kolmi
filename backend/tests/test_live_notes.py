from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from fastapi import HTTPException

from app.actions import get_registry, invoke
from app.actions import live_notes as live
from app.auth import Context


class _Query:
    def __init__(self, store, name, op="select", data=None):
        self.store, self.name, self.op, self.data = store, name, op, data
        self.eqs: list[tuple[str, Any]] = []
        self.either: tuple[str, str] | None = None
        self.ins: list[tuple[str, list]] = []

    def select(self, *_a, **_k): return self
    def eq(self, column, value): self.eqs.append((column, value)); return self
    def order(self, *_a, **_k): return self
    def limit(self, _n): return self
    def in_(self, column, values): self.ins.append((column, list(values))); return self

    def or_(self, text):
        # Only the shape the list uses: "shared.eq.true,author_id.eq.<id>".
        self.either = text
        return self

    def _match(self, row):
        if not all(row.get(c) == v for c, v in self.eqs):
            return False
        if not all(row.get(c) in vs for c, vs in self.ins):
            return False
        if self.either:
            keep = False
            for part in self.either.split(","):
                column, _op, value = part.split(".", 2)
                keep = keep or str(row.get(column)).lower() == value
            return keep
        return True

    def execute(self):
        rows = self.store.setdefault(self.name, [])
        if self.op == "insert":
            row = {"id": len(rows) + 1, "ended_at": None, **self.data}
            rows.append(row)
            return SimpleNamespace(data=[dict(row)])
        hit = [r for r in rows if self._match(r)]
        if self.op == "update":
            for r in hit:
                r.update(self.data)
        if self.op == "delete":
            for r in hit:
                rows.remove(r)
        out = []
        for r in hit:
            r = dict(r)
            if self.name == "live_notes":
                r["profiles"] = {"name": self.store.get("names", {}).get(r["author_id"])}
            out.append(r)
        return SimpleNamespace(data=out)


class _Client:
    def __init__(self, store):
        self.store = store

    def table(self, name):
        return _Table(self.store, name)


class _Table:
    def __init__(self, store, name): self.store, self.name = store, name
    def select(self, *_a, **_k): return _Query(self.store, self.name)
    def insert(self, data): return _Query(self.store, self.name, "insert", data)
    def update(self, data): return _Query(self.store, self.name, "update", data)
    def delete(self): return _Query(self.store, self.name, "delete")


NAMES = {"ana": "Ana", "luis": "Luis", "root": "Root"}


@pytest.fixture
def store(monkeypatch):
    data: dict[str, Any] = {"names": NAMES}
    # The timetable is its own concern: these tests say what is on, or that nothing is.
    monkeypatch.setattr(live, "current_class", lambda _client: data.get("on_now"))
    # Who is following lives in memory: every test starts with nobody.
    monkeypatch.setattr(live, "_seen", {})
    data["profiles"] = [{"id": u, "name": n, "status": "active"} for u, n in NAMES.items()]
    return data


def _ctx(store, user="ana", role="student") -> Context:
    profile = {"id": user, "name": NAMES[user], "role": role, "status": "active"}
    return Context(user_id=user, email=None, profile=profile, client=_Client(store))  # type: ignore[arg-type]


def run(name, ctx, args=None):
    return invoke(get_registry()[name], ctx, args)


def _ago(minutes: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()


def _seed(store, **fields):
    rows = store.setdefault("live_notes", [])
    row = {
        "id": len(rows) + 1, "author_id": "ana", "title": "Deployment", "event_id": None,
        "content": "", "shared": True, "ended_at": None, "created_at": _ago(10), "updated_at": _ago(1),
        **fields,
    }
    rows.append(row)
    return row


# -- starting, saving, ending ---------------------------------------------------------


def test_start_takes_the_title_and_the_class_on_now(store):
    store["on_now"] = {"event_id": 7, "title": "Deployment"}

    note = run("start_live_note", _ctx(store), {})

    assert note["title"] == "Deployment"
    assert note["shared"] is False and note["mine"] is True
    assert store["live_notes"][0]["event_id"] == 7
    assert store["live_notes"][0]["author_id"] == "ana"


def test_start_prefers_the_title_the_writer_gives(store):
    store["on_now"] = {"event_id": 7, "title": "Deployment"}

    note = run("start_live_note", _ctx(store), {"title": "  Docker deep dive "})

    assert note["title"] == "Docker deep dive"
    assert store["live_notes"][0]["event_id"] == 7


def test_start_with_no_class_on_needs_a_title(store):
    with pytest.raises(HTTPException) as err:
        run("start_live_note", _ctx(store), {})

    assert err.value.status_code == 422
    assert "title" in err.value.detail
    assert run("start_live_note", _ctx(store), {"title": "Extra"})["title"] == "Extra"
    assert store["live_notes"][0]["event_id"] is None


def test_start_can_mirror_one_of_my_notes(store):
    store["notes"] = [{"id": 5, "user_id": "ana"}]

    note = run("start_live_note", _ctx(store), {"note_id": 5, "title": "Docker", "content": "# Docker", "shared": True})

    row = store["live_notes"][0]
    assert row["note_id"] == 5 and row["content"] == "# Docker" and row["shared"] is True
    assert note["note_id"] == 5 and note["title"] == "Docker"


def test_a_linked_session_without_a_title_is_untitled(store):
    store["notes"] = [{"id": 5, "user_id": "ana"}]

    assert run("start_live_note", _ctx(store), {"note_id": 5})["title"] == "Untitled"


def test_start_refuses_a_note_that_is_not_mine(store):
    store["notes"] = [{"id": 5, "user_id": "luis"}]

    with pytest.raises(HTTPException) as err:
        run("start_live_note", _ctx(store), {"note_id": 5, "title": "x"})

    assert err.value.status_code == 404
    assert not store.get("live_notes")


def test_starting_ends_my_other_open_session_and_nobody_elses(store):
    store["notes"] = [{"id": 5, "user_id": "ana"}]
    _seed(store, author_id="ana")
    _seed(store, author_id="luis")
    _seed(store, author_id="ana", ended_at=_ago(30))

    run("start_live_note", _ctx(store), {"note_id": 5, "title": "x"})

    rows = store["live_notes"]
    assert rows[0]["ended_at"] is not None
    assert rows[1]["ended_at"] is None
    assert rows[3]["ended_at"] is None


def test_the_link_to_the_note_is_only_shown_to_its_author(store):
    _seed(store, note_id=5)

    assert run("read_live_note", _ctx(store), {"id": 1})["note_id"] == 5
    assert run("read_live_note", _ctx(store, "luis"), {"id": 1})["note_id"] is None
    assert run("list_live_notes", _ctx(store, "luis"))["notes"][0]["note_id"] is None
    assert run("list_live_notes", _ctx(store))["notes"][0]["note_id"] == 5


def test_save_writes_the_text_and_shares_it(store):
    _seed(store, shared=False, updated_at=_ago(30))

    out = run("save_live_note", _ctx(store), {"id": 1, "content": "# Docker", "shared": True})

    row = store["live_notes"][0]
    assert row["content"] == "# Docker" and row["shared"] is True
    assert row["updated_at"] == out["updated_at"] and out["shared"] is True
    assert datetime.fromisoformat(row["updated_at"]) > datetime.now(timezone.utc) - timedelta(minutes=1)


def test_save_leaves_out_what_is_not_given(store):
    _seed(store, content="old", shared=True)

    run("save_live_note", _ctx(store), {"id": 1, "content": "new"})

    assert store["live_notes"][0]["shared"] is True
    with pytest.raises(HTTPException) as err:
        run("save_live_note", _ctx(store), {"id": 1})
    assert err.value.status_code == 422


def test_only_the_author_writes_even_an_admin(store):
    _seed(store)

    for user, role in (("luis", "student"), ("root", "admin")):
        for name, args in (("save_live_note", {"id": 1, "content": "x"}), ("end_live_note", {"id": 1})):
            with pytest.raises(HTTPException) as err:
                run(name, _ctx(store, user, role), args)
            assert err.value.status_code == 403
    assert store["live_notes"][0]["content"] == ""


def test_an_ended_note_cannot_be_saved(store):
    _seed(store, ended_at=_ago(2))

    with pytest.raises(HTTPException) as err:
        run("save_live_note", _ctx(store), {"id": 1, "content": "x"})

    assert err.value.status_code == 409
    assert "start_live_note" in err.value.detail


def test_a_session_ends_by_itself_after_three_hours(store):
    long_ago = live.MAX_SESSION.total_seconds() / 60 + 5
    _seed(store, created_at=_ago(long_ago), updated_at=_ago(1))

    assert not live.is_live(store["live_notes"][0])
    shown = run("read_live_note", _ctx(store), {"id": 1})
    assert shown["ended"] is True and shown["live"] is False
    with pytest.raises(HTTPException) as err:
        run("save_live_note", _ctx(store), {"id": 1, "content": "x"})
    assert err.value.status_code == 409
    # The record is closed at the moment the limit was reached.
    assert store["live_notes"][0]["ended_at"] is not None


def test_end_sets_ended_at_once(store):
    _seed(store)

    first = run("end_live_note", _ctx(store), {"id": 1})
    second = run("end_live_note", _ctx(store), {"id": 1})

    assert store["live_notes"][0]["ended_at"] == first["ended_at"] == second["ended_at"]


def test_a_missing_note_says_how_to_find_one(store):
    with pytest.raises(HTTPException) as err:
        run("end_live_note", _ctx(store), {"id": 9})

    assert err.value.status_code == 404
    assert "list_live_notes" in err.value.detail


# -- reading --------------------------------------------------------------------------


def test_read_returns_the_note_for_any_member(store):
    row = _seed(store, content="Docker notes")

    note = run("read_live_note", _ctx(store, "luis"), {"id": 1})

    assert note["content"] == "Docker notes"
    assert note["author"] == "Ana" and note["mine"] is False
    assert note["live"] is True and note["ended"] is False
    assert note["updated_at"] == row["updated_at"] and note["unchanged"] is False


def test_read_with_the_same_since_is_a_tiny_answer(store):
    row = _seed(store, content="x" * 5000)

    out = run("read_live_note", _ctx(store, "luis"), {"id": 1, "since": row["updated_at"]})

    assert out == {"id": 1, "unchanged": True, "updated_at": row["updated_at"], "live": True, "ended": False, "followers": [{"id": "luis", "name": "Luis", "avatar_url": None}]}


def test_read_with_an_older_since_returns_the_text(store):
    _seed(store, content="more")

    out = run("read_live_note", _ctx(store, "luis"), {"id": 1, "since": _ago(60)})

    assert out["content"] == "more"


def test_an_unshared_note_is_only_the_authors(store):
    _seed(store, shared=False, content="draft")

    assert run("read_live_note", _ctx(store), {"id": 1})["content"] == "draft"
    with pytest.raises(HTTPException) as err:
        run("read_live_note", _ctx(store, "luis"), {"id": 1})
    assert err.value.status_code == 404


def test_a_note_is_live_only_when_shared_open_and_recent(store):
    assert live.is_live({"shared": True, "ended_at": None, "updated_at": _ago(1)})
    assert not live.is_live({"shared": False, "ended_at": None, "updated_at": _ago(1)})
    assert not live.is_live({"shared": True, "ended_at": _ago(1), "updated_at": _ago(1)})
    stale = live.LIVE_WINDOW.total_seconds() / 60 + 1
    assert not live.is_live({"shared": True, "ended_at": None, "updated_at": _ago(stale)})


# -- listing --------------------------------------------------------------------------


def test_the_list_puts_what_is_live_first(store):
    _seed(store, title="Old", updated_at=_ago(2000), ended_at=_ago(1990), content="finished")
    _seed(store, title="Now", content="a" * 300)
    _seed(store, title="Abandoned", updated_at=_ago(60))
    store["on_now"] = {"event_id": 3, "title": "Databases"}

    out = run("list_live_notes", _ctx(store, "luis"))

    assert [n["title"] for n in out["notes"]][0] == "Now"
    assert [n["live"] for n in out["notes"]] == [True, False, False]
    assert out["notes"][0]["author"] == "Ana"
    assert len(out["notes"][0]["preview"]) == live.PREVIEW_CHARS
    assert "content" not in out["notes"][0]
    assert out["current_class"] == {"event_id": 3, "title": "Databases"}


def test_the_list_hides_unshared_notes_but_the_authors(store):
    _seed(store, title="Private", shared=False)
    _seed(store, title="Public")

    assert [n["title"] for n in run("list_live_notes", _ctx(store, "luis"))["notes"]] == ["Public"]
    mine = run("list_live_notes", _ctx(store))["notes"]
    assert {n["title"] for n in mine} == {"Private", "Public"}
    assert all(n["mine"] for n in mine)


def test_the_list_is_empty_and_quiet(store):
    assert run("list_live_notes", _ctx(store)) == {"notes": [], "current_class": None}


# -- deleting -------------------------------------------------------------------------


def test_the_author_and_an_admin_delete_nobody_else(store):
    _seed(store)
    _seed(store)
    _seed(store)

    with pytest.raises(HTTPException) as err:
        run("delete_live_note", _ctx(store, "luis"), {"id": 1})
    assert err.value.status_code == 403
    assert run("delete_live_note", _ctx(store), {"id": 1}) == {"ok": True}
    assert run("delete_live_note", _ctx(store, "root", "admin"), {"id": 2}) == {"ok": True}
    assert [r["id"] for r in store["live_notes"]] == [3]


# -- who may and where it is offered --------------------------------------------------


def test_a_blocked_or_pending_member_cannot_use_any_of_it(store):
    _seed(store)
    for status in ("blocked", "pending"):
        ctx = _ctx(store)
        ctx.profile["status"] = status
        for name in ("list_live_notes", "read_live_note", "start_live_note", "save_live_note"):
            with pytest.raises(HTTPException) as err:
                run(name, ctx, {"id": 1, "title": "x", "content": "x"})
            assert err.value.status_code == 403


def test_reads_are_tools_and_mcp_writes_are_neither():
    registry = get_registry()
    for name in ("list_live_notes", "read_live_note"):
        assert registry[name].read_only and registry[name].tool and registry[name].mcp
    for name in ("start_live_note", "save_live_note", "end_live_note", "delete_live_note"):
        assert not registry[name].read_only
        assert not registry[name].tool and not registry[name].mcp


# -- the timetable --------------------------------------------------------------------


class _Rows:
    def __init__(self, rows): self.rows = rows
    def select(self, *_a): return self
    def eq(self, column, value): return _Rows([r for r in self.rows if r.get(column) == value])
    def limit(self, _n): return self
    def execute(self): return SimpleNamespace(data=self.rows)


class _TimetableClient:
    def __init__(self, events, nodes=()):
        self.tables = {"schedule_events": list(events), "nodes": list(nodes)}

    def table(self, name): return _Rows(self.tables[name])


def _on(monkeypatch, when: datetime, **settings):
    base = {"schedule_enabled": True, "schedule_days": [1, 3, 5]}
    monkeypatch.setattr(live, "read_settings", lambda _c: {**base, **settings})

    class Frozen(datetime):
        @classmethod
        def now(cls, tz=None):
            return when.astimezone(tz) if tz else when

    monkeypatch.setattr(live, "datetime", Frozen)


def test_the_class_on_now_comes_from_the_timetable(monkeypatch):
    # Wednesday 14 Oct 2026, 10:15 in Madrid: the second chosen day (index 1).
    _on(monkeypatch, datetime(2026, 10, 14, 10, 15, tzinfo=ZoneInfo("Europe/Madrid")))
    client = _TimetableClient(
        [
            {"id": 1, "day": 0, "start_time": "10:00", "end_time": "11:00", "title": "Monday's"},
            {"id": 2, "day": 1, "start_time": "09:00", "end_time": "10:00", "title": "Earlier"},
            {"id": 3, "day": 1, "start_time": "10:00", "end_time": "11:00", "title": None, "node_id": 5},
        ],
        [{"id": 5, "title": "Deployment"}],
    )

    assert live.current_class(client) == {"event_id": 3, "title": "Deployment"}


def test_no_class_on_when_off_between_slots_or_on_a_free_day(monkeypatch):
    slot = {"id": 1, "day": 1, "start_time": "10:00", "end_time": "11:00", "title": "X"}
    madrid = ZoneInfo("Europe/Madrid")

    _on(monkeypatch, datetime(2026, 10, 14, 11, 0, tzinfo=madrid))  # the end is not inside
    assert live.current_class(_TimetableClient([slot])) is None
    _on(monkeypatch, datetime(2026, 10, 14, 10, 15, tzinfo=madrid), schedule_enabled=False)
    assert live.current_class(_TimetableClient([slot])) is None
    _on(monkeypatch, datetime(2026, 10, 13, 10, 15, tzinfo=madrid))  # Tuesday is not a class day
    assert live.current_class(_TimetableClient([slot])) is None


# -- who is following ------------------------------------------------------------------


def _read(store, user, **args):
    return run("read_live_note", _ctx(store, user), {"id": 1, **args})


def test_a_reader_shows_as_follower_and_the_author_does_not(store, monkeypatch):
    _seed(store)
    assert _read(store, "ana")["followers"] == []
    out = _read(store, "luis")
    assert out["followers"] == [{"id": "luis", "name": "Luis", "avatar_url": None}]
    # The author's own read learns who is here, and is not counted among them.
    assert _read(store, "ana")["followers"] == [{"id": "luis", "name": "Luis", "avatar_url": None}]


def test_followers_come_with_the_unchanged_answer(store):
    row = _seed(store)
    _read(store, "luis")
    out = _read(store, "root", since=row["updated_at"])
    assert out["unchanged"] is True
    assert {f["id"] for f in out["followers"]} == {"luis", "root"}


def test_a_follower_drops_out_after_the_window(store, monkeypatch):
    _seed(store)
    clock = [1000.0]
    monkeypatch.setattr(live.time, "monotonic", lambda: clock[0])
    _read(store, "luis")
    clock[0] += live.FOLLOW_WINDOW - 1
    assert [f["id"] for f in _read(store, "ana")["followers"]] == ["luis"]
    clock[0] += 2
    assert _read(store, "ana")["followers"] == []
    assert live._seen == {}


def test_only_active_members_are_named(store):
    _seed(store)
    _read(store, "luis")
    _read(store, "root")
    next(p for p in store["profiles"] if p["id"] == "luis")["status"] = "blocked"
    assert [f["name"] for f in _read(store, "ana")["followers"]] == ["Root"]


def test_followers_are_capped_with_the_full_count(store, monkeypatch):
    _seed(store)
    for i in range(live.MAX_FOLLOWERS + 5):
        store["profiles"].append({"id": f"u{i}", "name": f"U{i}", "status": "active"})
        live._seen.setdefault(1, {})[f"u{i}"] = live.time.monotonic()
    out = _read(store, "ana")
    assert len(out["followers"]) == live.MAX_FOLLOWERS
    assert out["followers_count"] == live.MAX_FOLLOWERS + 5

def test_no_count_under_the_cap(store):
    _seed(store)
    assert "followers_count" not in _read(store, "luis")
