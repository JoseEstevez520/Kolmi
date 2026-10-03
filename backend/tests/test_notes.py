from __future__ import annotations

from typing import Any

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.actions.notes import (
    CreateNoteParams,
    UpdateNoteParams,
    create_note,
    update_note,
)
from app.auth import Context


class _Query:
    """One chained call on the fake table: insert, select or update, then filters."""

    def __init__(self, table: _Table, op: str, data: dict[str, Any] | None = None) -> None:
        self.table = table
        self.op = op
        self.data = data
        self.filters: list[tuple[str, Any]] = []

    def eq(self, column: str, value: Any) -> _Query:
        self.filters.append((column, value))
        return self

    def limit(self, _n: int) -> _Query:
        return self

    def order(self, _column: str, desc: bool = False) -> _Query:
        return self

    def in_(self, column: str, values: list[Any]) -> _Query:
        self.members = (column, values)
        return self

    def _matches(self) -> list[dict[str, Any]]:
        found = [r for r in self.table.rows if all(r.get(c) == v for c, v in self.filters)]
        if getattr(self, "members", None):
            column, values = self.members
            found = [r for r in found if r.get(column) in values]
        return found

    def execute(self) -> Any:
        if self.op == "insert":
            stored = {"id": len(self.table.rows) + 1, "status": "pending", **self.data}
            self.table.rows.append(stored)
            found = [stored]
        elif self.op == "update":
            found = self._matches()
            for row in found:
                row.update(self.data)
        else:
            found = self._matches()
        return type("Response", (), {"data": [dict(r) for r in found]})()


class _Table:
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []

    def insert(self, row: dict[str, Any]) -> _Query:
        return _Query(self, "insert", row)

    def select(self, _columns: str) -> _Query:
        return _Query(self, "select")

    def update(self, data: dict[str, Any]) -> _Query:
        return _Query(self, "update", data)


class _Client:
    """Just enough of the Supabase client for the notes table (and the nodes a hint names)."""

    def __init__(self) -> None:
        self.notes = _Table()
        self.nodes = _Table()
        self.nodes.rows = [{"id": 20}, {"id": 31}]
        self.files = _Table()

    def table(self, name: str) -> _Table:
        assert name in ("notes", "nodes", "files")
        return getattr(self, name)


def _ctx(client: _Client, user_id: str = "u1") -> Context:
    return Context(user_id=user_id, email=None, profile={"approved": True}, client=client)


def test_a_note_is_plain_text_by_default():
    client = _Client()
    create_note(_ctx(client), CreateNoteParams(content="git stash keeps my changes"))
    assert client.notes.rows[0]["format"] == "text"


def test_a_note_from_the_editor_keeps_its_markdown():
    client = _Client()
    content = "## Git\n\n- `git stash` keeps my changes"
    note = create_note(_ctx(client), CreateNoteParams(content=content, format="markdown"))
    assert note["format"] == "markdown"
    assert note["content"] == content


def test_an_unknown_format_is_refused():
    with pytest.raises(ValidationError):
        CreateNoteParams(content="hi", format="html")


def _pending_note(client: _Client) -> int:
    return create_note(_ctx(client), CreateNoteParams(content="first draft"))["id"]


def test_a_pending_note_can_be_rewritten():
    client = _Client()
    note_id = _pending_note(client)
    note = update_note(_ctx(client), UpdateNoteParams(note_id=note_id, content="# Git\n\nbetter"))
    assert note["content"] == "# Git\n\nbetter"
    assert note["format"] == "markdown"


def test_someone_elses_note_looks_missing():
    client = _Client()
    note_id = _pending_note(client)
    with pytest.raises(HTTPException) as error:
        update_note(_ctx(client, "u2"), UpdateNoteParams(note_id=note_id, content="mine now"))
    assert error.value.status_code == 404
    assert client.notes.rows[0]["content"] == "first draft"


def test_a_note_the_pass_took_is_closed():
    client = _Client()
    note_id = _pending_note(client)
    client.notes.rows[0]["status"] = "processed"
    with pytest.raises(HTTPException) as error:
        update_note(_ctx(client), UpdateNoteParams(note_id=note_id, content="too late"))
    assert error.value.status_code == 409


def test_a_note_can_say_where_it_goes():
    client = _Client()
    note = create_note(_ctx(client), CreateNoteParams(content="git stash", node_id=20))
    assert note["node_id"] == 20


def test_a_hint_to_a_missing_node_is_refused():
    client = _Client()
    with pytest.raises(HTTPException) as error:
        create_note(_ctx(client), CreateNoteParams(content="git stash", node_id=99))
    assert error.value.status_code == 422
    assert client.notes.rows == []


def test_the_hint_can_change_while_the_note_is_pending():
    client = _Client()
    note_id = create_note(_ctx(client), CreateNoteParams(content="draft", node_id=20))["id"]

    note = update_note(_ctx(client), UpdateNoteParams(note_id=note_id, content="draft", node_id=31))
    assert note["node_id"] == 31

    # Left out, it stays; null clears it ("Not sure").
    note = update_note(_ctx(client), UpdateNoteParams(note_id=note_id, content="again"))
    assert note["node_id"] == 31
    note = update_note(_ctx(client), UpdateNoteParams(note_id=note_id, content="x", node_id=None))
    assert note["node_id"] is None

    with pytest.raises(HTTPException) as error:
        update_note(_ctx(client), UpdateNoteParams(note_id=note_id, content="x", node_id=99))
    assert error.value.status_code == 422
    assert client.notes.rows[0]["node_id"] is None


def test_a_note_with_nothing_in_it_is_not_created():
    client = _Client()
    for content in ("", "  \n "):
        with pytest.raises(HTTPException) as error:
            create_note(_ctx(client), CreateNoteParams(content=content))
        assert error.value.status_code == 422
    assert client.notes.rows == []


def test_a_note_can_be_created_empty_for_its_files():
    client = _Client()
    note = create_note(_ctx(client), CreateNoteParams(for_files=True))
    assert note["content"] == ""
    assert len(client.notes.rows) == 1


def test_a_note_cannot_be_emptied_unless_it_has_files():
    client = _Client()
    note_id = _pending_note(client)
    with pytest.raises(HTTPException) as error:
        update_note(_ctx(client), UpdateNoteParams(note_id=note_id, content=" "))
    assert error.value.status_code == 422
    assert client.notes.rows[0]["content"] == "first draft"

    client.files.rows.append({"id": 1, "note_id": note_id})
    note = update_note(_ctx(client), UpdateNoteParams(note_id=note_id, content=""))
    assert note["content"] == ""


def test_my_notes_carry_their_file_names():
    from app.actions.notes import MyNotesParams, my_notes

    client = _Client()
    note = create_note(_ctx(client), CreateNoteParams(for_files=True))
    client.files.rows.append({"id": 7, "note_id": note["id"], "name": "slides.pdf", "size": 10})
    notes = my_notes(_ctx(client), MyNotesParams())
    assert notes[0]["files"] == [{"id": 7, "name": "slides.pdf", "size": 10}]
