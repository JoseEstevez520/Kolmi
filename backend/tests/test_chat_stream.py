"""The streaming chat: server-sent events, the same checks and proposals as ask_chat."""

from __future__ import annotations

import json

import pytest
from fastapi import HTTPException

from app.actions.chat import AskChatParams, stream_chat
from tests.fakes import FakeLLM
from tests.test_chat_tools import _Client, _ctx

PROGRAM = ['root = Answer([a, b])\n', 'a = Text("Use `git stash`.")\n', "b = Sources([20])"]


def _events(raw: list[str]) -> list[tuple[str, dict]]:
    out = []
    for chunk in raw:
        assert chunk.endswith("\n\n")
        head, data = chunk.strip().split("\n")
        assert head.startswith("event: ") and data.startswith("data: ")
        out.append((head[7:], json.loads(data[6:])))
    return out


def _stream(monkeypatch, client, llm, question="help me", role="student"):
    monkeypatch.setattr("app.actions.chat.get_chat_llm", lambda: llm)
    monkeypatch.setattr("app.agents.search.web_search", lambda q: "")
    return _events(list(stream_chat(_ctx(client, role), AskChatParams(question=question))))


def test_tokens_stream_then_done(monkeypatch):
    client = _Client()
    llm = FakeLLM()
    llm.stream_tokens = PROGRAM
    events = _stream(monkeypatch, client, llm)

    assert [name for name, _ in events] == ["token"] * 3 + ["done"]
    assert events[0][1] == {"text": PROGRAM[0]}
    assert events[-1] == ("done", {})
    [message] = client.rows("chat_messages")
    assert message["answer"] == "".join(PROGRAM)
    assert message["sources"] == [20]
    assert llm.calls[0][0] == "stream"
    assert "Answer([" in llm.calls[0][1]


def test_a_write_is_proposed_with_its_id_and_never_run(monkeypatch):
    client = _Client()
    llm = FakeLLM(tool_rounds=[[("create_note", {"content": "git stash keeps my changes"})]])
    llm.stream_tokens = ["root = Answer([Proposal(1)])"]
    events = _stream(monkeypatch, client, llm)

    names = [name for name, _ in events]
    assert names == ["status", "token", "proposal", "done"]
    [row] = client.rows("chat_proposals")
    assert row["status"] == "pending"
    assert client.rows("notes") == []
    assert events[2][1] == {
        "id": row["id"],
        "tool": "create_note",
        "args": {"content": "git stash keeps my changes"},
        "status": "pending",
        "destructive": False,
        "result": None,
    }
    assert f"Proposal({row['id']})" in llm.tool_results[0]


def test_a_failure_ends_with_error_and_keeps_what_was_written(monkeypatch):
    client = _Client()
    llm = FakeLLM()
    llm.stream_tokens = ["root = Answer(["]
    llm.stream_error = RuntimeError("boom")
    events = _stream(monkeypatch, client, llm)

    assert [name for name, _ in events] == ["token", "error"]
    assert "message" in events[-1][1]
    assert "boom" not in events[-1][1]["message"]
    assert client.rows("chat_messages")[0]["answer"] == "root = Answer(["


def test_an_empty_answer_is_an_error(monkeypatch):
    events = _stream(monkeypatch, _Client(), FakeLLM())
    assert [name for name, _ in events] == ["error"]


def test_the_checks_fail_before_anything_streams(monkeypatch):
    client = _Client()
    client.rows("settings")[0]["chat_daily_limit"] = 0
    with pytest.raises(HTTPException) as limit:
        _stream(monkeypatch, client, FakeLLM())
    assert limit.value.status_code == 429

    client = _Client()
    client.rows("settings")[0]["chat_enabled"] = False
    with pytest.raises(HTTPException) as off:
        _stream(monkeypatch, client, FakeLLM())
    assert off.value.status_code == 403

    with pytest.raises(HTTPException) as empty:
        _stream(monkeypatch, _Client(), FakeLLM(), question="  ")
    assert empty.value.status_code == 422
