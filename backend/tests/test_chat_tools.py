"""The chat uses the class's actions as tools: reads run inside its loop, anything else is a
proposal the person confirms (or cancels) in a new request, run then through `invoke`."""

from __future__ import annotations

import dataclasses
from datetime import datetime, timezone
from typing import Any

import pytest
from fastapi import HTTPException

from app.actions import get_registry
from app.actions.registry import get_action, invoke
from app.auth import Context
from app.actions.tools import chat_tool
from tests.fakes import FakeLLM

ANSWER = {"answer": "Done.", "sources": []}
NODES = [
    {"id": 10, "parent_id": None, "kind": "section", "title": "Tools", "position": 0},
    {"id": 20, "parent_id": 10, "kind": "page", "title": "Git", "position": 0, "content_md": "# Git"},
]


# --- An in-memory Supabase client -------------------------------------------------------------


class _Response:
    def __init__(self, data: Any, count: int | None = None) -> None:
        self.data = data
        self.count = count


class _Query:
    """One chained call on a fake table: select, insert, update, upsert or delete, then filters."""

    def __init__(self, table: _Table, op: str, data: Any = None, count: str | None = None) -> None:
        self.table = table
        self.op = op
        self.data = data
        self.count = count
        self.filters: list[Any] = []
        self._limit: int | None = None
        self._single = False

    def eq(self, column: str, value: Any) -> _Query:
        self.filters.append(lambda r: r.get(column) == value)
        return self

    def neq(self, column: str, value: Any) -> _Query:
        self.filters.append(lambda r: r.get(column) != value)
        return self

    def in_(self, column: str, values: list[Any]) -> _Query:
        self.filters.append(lambda r: r.get(column) in list(values))
        return self

    def is_(self, column: str, value: Any) -> _Query:
        wanted = None if value in (None, "null") else value
        self.filters.append(lambda r: r.get(column) is wanted)
        return self

    def gte(self, column: str, value: Any) -> _Query:
        # Dates come in more than one shape: a row without the column, or one not comparable, counts.
        def keep(r: dict[str, Any]) -> bool:
            try:
                return r.get(column) is None or r.get(column) >= value
            except TypeError:
                return True

        self.filters.append(keep)
        return self

    def order(self, _column: str, desc: bool = False) -> _Query:
        return self

    def limit(self, n: int) -> _Query:
        self._limit = n
        return self

    def range(self, start: int, end: int) -> _Query:
        return self

    def single(self) -> _Query:
        self._single = True
        return self

    maybe_single = single

    def _matches(self) -> list[dict[str, Any]]:
        return [r for r in self.table.rows if all(f(r) for f in self.filters)]

    def execute(self) -> _Response:
        if self.op in ("insert", "upsert"):
            rows = self.data if isinstance(self.data, list) else [self.data]
            found = [self.table.add(row) for row in rows]
        elif self.op == "update":
            found = self._matches()
            for row in found:
                row.update(self.data)
        elif self.op == "delete":
            found = self._matches()
            self.table.rows = [r for r in self.table.rows if r not in found]
        else:
            found = self._matches()
            if self._limit is not None:
                found = found[: self._limit]
        data = [dict(r) for r in found]
        if self._single:
            return _Response(data[0] if data else None)
        return _Response(data, len(data) if self.count else None)


class _Table:
    def __init__(self, name: str, rows: list[dict[str, Any]] | None = None) -> None:
        self.name = name
        self.rows = [dict(r) for r in rows or []]

    def add(self, row: dict[str, Any]) -> dict[str, Any]:
        next_id = max([r.get("id", 0) for r in self.rows if isinstance(r.get("id"), int)] + [0]) + 1
        defaults = {"id": next_id, "created_at": datetime.now(timezone.utc).isoformat()}
        if self.name in ("notes", "chat_proposals"):
            defaults["status"] = "pending"
        stored = {**defaults, **row}
        self.rows.append(stored)
        return stored

    def select(self, *_columns: str, count: str | None = None) -> _Query:
        return _Query(self, "select", count=count)

    def insert(self, data: Any) -> _Query:
        return _Query(self, "insert", data)

    def upsert(self, data: Any, **_kwargs: Any) -> _Query:
        return _Query(self, "upsert", data)

    def update(self, data: dict[str, Any]) -> _Query:
        return _Query(self, "update", data)

    def delete(self) -> _Query:
        return _Query(self, "delete")


class _Client:
    """Every table the chat and its tools touch, in memory; the class has the chat on."""

    def __init__(self) -> None:
        self.tables: dict[str, _Table] = {
            "settings": _Table("settings", [{"id": 1, "class_language": "en", "chat_enabled": True, "chat_daily_limit": 100}]),
            "nodes": _Table("nodes", NODES),
        }

    def table(self, name: str) -> _Table:
        return self.tables.setdefault(name, _Table(name))

    def rows(self, name: str) -> list[dict[str, Any]]:
        return self.table(name).rows


def _ctx(client: _Client, role: str = "student", user_id: str = "u1") -> Context:
    profile = {"id": user_id, "role": role, "status": "active", "approved": True}
    return Context(user_id=user_id, email=None, profile=profile, client=client)  # type: ignore[arg-type]


def _ask(monkeypatch, client: _Client, rounds, role: str = "student", user_id: str = "u1"):
    llm = FakeLLM(json_response=ANSWER, tool_rounds=rounds)
    monkeypatch.setattr("app.actions.chat.get_llm", lambda: llm)
    # The open web is never reached: no test asks for it, and this makes sure.
    monkeypatch.setattr("app.agents.search.web_search", lambda q: "")
    result = invoke(get_action("ask_chat"), _ctx(client, role, user_id), {"question": "help me"})
    return result, llm


def _confirm(client: _Client, proposal_id: int, args=None, role: str = "student", user_id: str = "u1"):
    return invoke(
        get_action("confirm_chat_proposal"),
        _ctx(client, role, user_id),
        {"proposal_id": proposal_id, "args": args},
    )


def _cancel(client: _Client, proposal_id: int, user_id: str = "u1"):
    return invoke(get_action("cancel_chat_proposal"), _ctx(client, user_id=user_id), {"proposal_id": proposal_id})


def _spy(monkeypatch, name: str) -> list[Context]:
    """Wrap an action's handler, recording the context it ran with."""
    seen: list[Context] = []
    original = get_registry()[name]

    def handler(ctx, params):
        seen.append(ctx)
        return original.handler(ctx, params)

    monkeypatch.setitem(get_registry(), name, dataclasses.replace(original, handler=handler))
    return seen


def _propose_note(monkeypatch, client: _Client, content: str = "git stash keeps my changes") -> int:
    result, _ = _ask(monkeypatch, client, [[("create_note", {"content": content})]])
    return result["proposals"][0]["id"]


# --- Reads run in the loop --------------------------------------------------------------------


def test_a_read_runs_inside_the_loop_and_reaches_the_model(monkeypatch):
    client = _Client()
    seen = _spy(monkeypatch, "list_nodes")
    result, llm = _ask(monkeypatch, client, [[("list_nodes", {})]])

    assert len(seen) == 1
    assert "Git" in llm.tool_results[0] and "Tools" in llm.tool_results[0]
    assert result["answer"] == ANSWER["answer"]
    assert result["proposals"] == []
    assert client.rows("chat_proposals") == []


def test_the_model_is_offered_its_reads_and_the_class_actions(monkeypatch):
    client = _Client()
    _, llm = _ask(monkeypatch, client, [])

    offered = set(llm.offered_tools[0])
    assert {"read_page", "list_nodes", "my_notes", "create_note"} <= offered


# --- Anything else is a proposal --------------------------------------------------------------


def test_a_write_stays_proposed(monkeypatch):
    client = _Client()
    result, llm = _ask(monkeypatch, client, [[("create_note", {"content": "git stash keeps my changes"})]])

    assert client.rows("notes") == []
    assert "propos" in llm.tool_results[0].lower()

    [row] = client.rows("chat_proposals")
    [message] = client.rows("chat_messages")
    assert row["status"] == "pending"
    assert row["tool"] == "create_note"
    assert row["args"] == {"content": "git stash keeps my changes"}
    assert row["user_id"] == "u1"
    assert row["message_id"] == message["id"] == result["message_id"]

    [proposal] = result["proposals"]
    assert proposal["id"] == row["id"]
    assert proposal["tool"] == "create_note"
    assert proposal["args"] == {"content": "git stash keeps my changes"}
    assert proposal["status"] == "pending"
    assert proposal["destructive"] is False
    assert proposal["result"] is None


def test_confirming_runs_it_through_invoke_as_the_chat(monkeypatch):
    client = _Client()
    proposal_id = _propose_note(monkeypatch, client)
    seen = _spy(monkeypatch, "create_note")

    _confirm(client, proposal_id)

    [ctx] = seen
    assert ctx.source == "chat"
    assert ctx.user_id == "u1"
    assert ctx.profile["role"] == "student"
    [note] = client.rows("notes")
    assert note["content"] == "git stash keeps my changes"
    assert note["source"] == "chat"
    [row] = client.rows("chat_proposals")
    assert row["status"] == "done"
    assert row["result"]


def test_confirming_with_edited_args_runs_the_edit(monkeypatch):
    client = _Client()
    proposal_id = _propose_note(monkeypatch, client)

    _confirm(client, proposal_id, args={"content": "git stash -u keeps untracked files too"})

    [note] = client.rows("notes")
    assert note["content"] == "git stash -u keeps untracked files too"
    assert client.rows("chat_proposals")[0]["status"] == "done"


def test_it_runs_with_the_confirmers_role_not_the_proposers(monkeypatch):
    client = _Client()
    result, _ = _ask(
        monkeypatch, client, [[("create_node", {"kind": "page", "title": "Rebase"})]], role="admin"
    )
    proposal_id = result["proposals"][0]["id"]

    # Demoted since: the confirmation is refused, and the proposal waits.
    with pytest.raises(HTTPException) as error:
        _confirm(client, proposal_id, role="student")
    assert error.value.status_code == 403
    assert [n["title"] for n in client.rows("nodes")] == ["Tools", "Git"]
    row = client.rows("chat_proposals")[0]
    assert row["status"] == "pending"

    _confirm(client, proposal_id, role="admin")
    assert "Rebase" in [n["title"] for n in client.rows("nodes")]
    assert client.rows("chat_proposals")[0]["status"] == "done"


# --- What a student isn't offered -------------------------------------------------------------


def test_a_student_is_not_offered_admin_tools(monkeypatch):
    client = _Client()
    _, llm = _ask(monkeypatch, client, [])

    offered = set(llm.offered_tools[0])
    assert "create_node" not in offered
    assert "write_page" not in offered


def test_an_admin_tool_a_student_asks_for_anyway_is_not_proposed(monkeypatch):
    client = _Client()
    result, llm = _ask(
        monkeypatch,
        client,
        [[("create_node", {"kind": "page", "title": "Rebase"}), ("write_page", {"node_id": 20, "content_md": "x"})]],
    )

    assert result["proposals"] == []
    assert client.rows("chat_proposals") == []
    assert [n["title"] for n in client.rows("nodes")] == ["Tools", "Git"]
    assert all("propos" not in text.lower() for text in llm.tool_results)


def test_a_proposal_with_bad_args_is_not_recorded(monkeypatch):
    client = _Client()
    result, llm = _ask(monkeypatch, client, [[("create_note", {"content": "hi", "format": "html"})]])

    assert result["proposals"] == []
    assert client.rows("chat_proposals") == []
    assert "422" in llm.tool_results[0]


# --- Once, and only by whoever it was proposed to ---------------------------------------------


def test_a_proposal_cannot_be_confirmed_twice(monkeypatch):
    client = _Client()
    proposal_id = _propose_note(monkeypatch, client)
    _confirm(client, proposal_id)

    with pytest.raises(HTTPException) as error:
        _confirm(client, proposal_id)
    assert error.value.status_code == 409
    assert len(client.rows("notes")) == 1


def test_someone_elses_proposal_looks_missing(monkeypatch):
    client = _Client()
    proposal_id = _propose_note(monkeypatch, client)

    with pytest.raises(HTTPException) as error:
        _confirm(client, proposal_id, user_id="u2")
    assert error.value.status_code == 404
    with pytest.raises(HTTPException) as error:
        _cancel(client, proposal_id, user_id="u2")
    assert error.value.status_code == 404
    assert client.rows("notes") == []
    assert client.rows("chat_proposals")[0]["status"] == "pending"


def test_a_missing_proposal_is_404(monkeypatch):
    client = _Client()
    with pytest.raises(HTTPException) as error:
        _confirm(client, 999)
    assert error.value.status_code == 404


def test_a_cancelled_proposal_cannot_be_confirmed(monkeypatch):
    client = _Client()
    proposal_id = _propose_note(monkeypatch, client)
    _cancel(client, proposal_id)
    assert client.rows("chat_proposals")[0]["status"] == "cancelled"

    with pytest.raises(HTTPException) as error:
        _confirm(client, proposal_id)
    assert error.value.status_code == 409
    with pytest.raises(HTTPException) as error:
        _cancel(client, proposal_id)
    assert error.value.status_code == 409
    assert client.rows("notes") == []


# --- Edited args are checked again ------------------------------------------------------------


def test_edited_args_are_validated_and_the_proposal_waits(monkeypatch):
    client = _Client()
    proposal_id = _propose_note(monkeypatch, client)

    with pytest.raises(HTTPException) as error:
        _confirm(client, proposal_id, args={"content": "hi", "format": "html"})
    assert error.value.status_code == 422
    assert client.rows("notes") == []
    row = client.rows("chat_proposals")[0]
    assert row["status"] == "pending"
    assert row["result"].startswith("Error 422")

    # Still there to confirm, as proposed.
    _confirm(client, proposal_id)
    assert len(client.rows("notes")) == 1


# --- A confirmation that never came back, and a flood of proposals ---------------------------


def test_a_stuck_running_proposal_is_released_after_a_while(monkeypatch):
    client = _Client()
    proposal_id = _propose_note(monkeypatch, client)
    row = client.rows("chat_proposals")[0]
    row["status"] = "running"
    row["decided_at"] = "2020-01-01T00:00:00+00:00"

    _confirm(client, proposal_id)

    assert len(client.rows("notes")) == 1
    assert client.rows("chat_proposals")[0]["status"] == "done"


def test_a_recent_running_proposal_is_not_claimed_twice(monkeypatch):
    client = _Client()
    proposal_id = _propose_note(monkeypatch, client)
    row = client.rows("chat_proposals")[0]
    row["status"] = "running"
    row["decided_at"] = datetime.now(timezone.utc).isoformat()

    with pytest.raises(HTTPException) as error:
        _confirm(client, proposal_id)

    assert error.value.status_code == 409
    assert client.rows("notes") == []


def test_the_chat_proposes_at_most_a_few_changes_on_one_answer():
    from app.actions.tools import MAX_PROPOSALS

    proposals: list = []
    ctx = _ctx(_Client())
    run = chat_tool(ctx, proposals)
    for i in range(MAX_PROPOSALS + 2):
        run("create_note", {"content": f"note {i}"})

    assert len(proposals) == MAX_PROPOSALS


def test_the_answer_from_the_index_is_not_told_it_can_propose():
    """When the loop fails the model answers from the index; it must not claim a proposal."""
    from app.agents.prompts import CHAT_ACTIONS

    llm = FakeLLM(json_response=ANSWER, tool_rounds=None)
    llm.complete_with_tools = lambda *a, **k: (_ for _ in ()).throw(ValueError("loop failed"))
    systems: list[str] = []
    original = llm.complete_json
    llm.complete_json = lambda system, user: (systems.append(system), original(system, user))[1]

    from app.agents.chat import run_chat

    answer = run_chat(
        llm, "make a note", [], read_page=lambda i: None, actions=[{"type": "function"}], run_action=lambda n, a: ""
    )

    assert answer.from_index and systems and CHAT_ACTIONS not in systems[0]
