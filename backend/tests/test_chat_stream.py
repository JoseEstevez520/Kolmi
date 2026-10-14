"""The streaming chat: server-sent events, the same checks and proposals as ask_chat."""

from __future__ import annotations

import json
import threading
import time

import pytest
from fastapi import HTTPException

from app.actions.chat import PING, AskChatParams, stream_chat, with_heartbeat
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

    assert [name for name, _ in events] == ["status"] + ["token"] * 3 + ["done"]
    assert events[1][1] == {"text": PROGRAM[0]}
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
    assert names == ["status", "status", "token", "proposal", "done"]
    [row] = client.rows("chat_proposals")
    assert row["status"] == "pending"
    assert client.rows("notes") == []
    assert events[3][1] == {
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

    assert [name for name, _ in events] == ["status", "token", "error"]
    assert "message" in events[-1][1]
    assert "boom" not in events[-1][1]["message"]
    assert client.rows("chat_messages")[0]["answer"] == "root = Answer(["


def test_an_empty_answer_is_an_error(monkeypatch):
    events = _stream(monkeypatch, _Client(), FakeLLM())
    assert [name for name, _ in events] == ["status", "error"]


def test_the_checks_fail_before_anything_streams(monkeypatch):
    client = _Client()
    client.rows("settings")[0]["chat_daily_limit"] = 0
    with pytest.raises(HTTPException) as limit:
        _stream(monkeypatch, client, FakeLLM())
    assert limit.value.status_code == 429

    # An admin has no limit.
    client = _Client()
    client.rows("settings")[0]["chat_daily_limit"] = 0
    admin = _stream(monkeypatch, client, FakeLLM(), role="admin")
    assert admin[-1][0] in ("done", "error")

    client = _Client()
    client.rows("settings")[0]["chat_enabled"] = False
    with pytest.raises(HTTPException) as off:
        _stream(monkeypatch, client, FakeLLM())
    assert off.value.status_code == 403

    with pytest.raises(HTTPException) as empty:
        _stream(monkeypatch, _Client(), FakeLLM(), question="  ")
    assert empty.value.status_code == 422


def _asked(monkeypatch, node_id):
    client = _Client()
    llm = FakeLLM()
    llm.stream_tokens = PROGRAM
    monkeypatch.setattr("app.actions.chat.get_chat_llm", lambda: llm)
    monkeypatch.setattr("app.agents.search.web_search", lambda q: "")
    params = AskChatParams(question="explain this", node_id=node_id)
    list(stream_chat(_ctx(client), params))
    return llm.calls[0][2]


def test_the_open_page_is_named_not_inlined(monkeypatch):
    user = _asked(monkeypatch, 20)
    assert "The person has this page open: Git (id 20). Read it with read_page" in user
    assert "# Git" not in user


def test_an_unknown_page_is_ignored(monkeypatch):
    assert "has this page open" not in _asked(monkeypatch, 999)
    assert "has this page open" not in _asked(monkeypatch, None)


def test_the_first_event_is_a_status_before_the_model_is_called(monkeypatch):
    client = _Client()
    llm = FakeLLM()
    llm.stream_tokens = PROGRAM
    monkeypatch.setattr("app.actions.chat.get_chat_llm", lambda: llm)
    monkeypatch.setattr("app.agents.search.web_search", lambda q: "")
    stream = stream_chat(_ctx(client), AskChatParams(question="help me"))

    name, data = _events([next(stream)])[0]
    assert name == "status" and data["text"]
    assert llm.calls == []
    assert client.rows("chat_messages") == []
    stream.close()


def test_a_failed_preparation_is_an_error_event_and_leaves_no_row(monkeypatch):
    client = _Client()
    llm = FakeLLM()
    llm.stream_tokens = PROGRAM

    def boom(*args, **kwargs):
        raise RuntimeError("embedding down")

    monkeypatch.setattr("app.actions.chat.search", boom)
    events = _stream(monkeypatch, client, llm)

    assert [name for name, _ in events] == ["status", "error"]
    assert "embedding down" not in events[-1][1]["message"]
    assert client.rows("chat_messages") == []
    assert llm.calls == []


def test_the_chat_is_not_offered_the_tools_its_prompt_already_covers(monkeypatch):
    client = _Client()
    llm = FakeLLM()
    llm.stream_tokens = PROGRAM
    _stream(monkeypatch, client, llm)
    assert "list_nodes" not in llm.offered_tools[0]
    assert "search_pages" not in llm.offered_tools[0]
    assert "read_page" in llm.offered_tools[0]


def test_the_heartbeat_pings_on_silence_and_passes_the_rest():
    def slow():
        yield "a"
        time.sleep(0.25)
        yield "b"

    out = list(with_heartbeat(slow(), interval=0.05))
    assert out[0] == "a" and out[-1] == "b"
    assert PING in out
    assert set(out) <= {"a", "b", PING}


def test_the_heartbeat_closes_the_source_when_the_reader_leaves():
    closed = threading.Event()

    def source():
        try:
            for i in range(1000):
                yield f"{i}"
                time.sleep(0.01)
        finally:
            closed.set()

    stream = with_heartbeat(source(), interval=0.05)
    assert next(stream) == "0"
    stream.close()
    assert closed.wait(2)
