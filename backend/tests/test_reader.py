"""Reading explanations share chat limits, without note edits or action tools."""
import pytest
from fastapi import HTTPException

from app.actions.chat import AskChatParams, stream_chat
from app.agents import openui
from tests.fakes import FakeLLM
from tests.test_chat_stream import _events
from tests.test_chat_tools import _Client, _ctx


def test_reader_glance_receives_source_context_without_write_or_image_tools(monkeypatch):
    client = _Client()
    llm = FakeLLM()
    llm.stream_tokens = ["Every service gets the same instance."]
    monkeypatch.setattr("app.actions.chat.get_chat_llm", lambda: llm)
    params = AskChatParams(question="singleton", note="Scope describes when Spring creates objects.", mode="reader")
    events = _events(list(stream_chat(_ctx(client), params)))
    assert events[-1] == ("done", {})
    call = llm.calls[0]
    assert "one or two short sentences" in call[1]
    assert "Source passage being read" in call[2]
    assert "Scope describes" in call[2]
    assert llm.offered_tools == [[]]
    assert client.rows("notes") == []
    assert client.rows("chat_proposals") == []


def test_reader_detail_builds_visual_in_place_and_stores_it(monkeypatch):
    from tests.test_web_agent import PIECE
    client = _Client()
    llm = FakeLLM()
    llm.stream_tokens = ['Compare the scopes.\n```kolmi-ai\nroot = Answer([a])\na = Artifact("Scopes", "Compare references with a request button", 300)\n```']
    llm.text_response = [PIECE]
    monkeypatch.setattr("app.actions.chat.get_chat_llm", lambda: llm)
    params = AskChatParams(question="singleton", mode="reader_detail", note="Singleton keeps one instance.")
    events = _events(list(stream_chat(_ctx(client), params)))
    names = [name for name, _ in events]
    assert names.index("text_done") < names.index("fix") < names.index("done")
    [fixed] = [data["program"] for name, data in events if name == "fix"]
    artifact = openui.parse(fixed.replace("Answer(", "Page(", 1)).args[0][0]
    assert artifact.args[3] == PIECE
    assert "Artifact" in llm.calls[0][1]
    assert fixed in client.rows("chat_messages")[0]["answer"]
    assert client.rows("notes") == []


@pytest.mark.parametrize("mode", ["reader", "reader_detail"])
def test_reader_obeys_class_chat_switch_and_daily_limit(mode):
    client = _Client()
    params = AskChatParams(question="scope", mode=mode)
    client.rows("settings")[0]["chat_enabled"] = False
    with pytest.raises(HTTPException) as disabled:
        stream_chat(_ctx(client), params)
    assert disabled.value.status_code == 403
    client.rows("settings")[0].update(chat_enabled=True, chat_daily_limit=0)
    with pytest.raises(HTTPException) as capped:
        stream_chat(_ctx(client), params)
    assert capped.value.status_code == 429


def test_question_from_reader_has_source_context_but_keeps_chat_tools(monkeypatch):
    client = _Client()
    llm = FakeLLM()
    llm.stream_tokens = ['root = Answer([t])\nt = Text("Explanation")']
    monkeypatch.setattr("app.actions.chat.get_chat_llm", lambda: llm)
    monkeypatch.setattr("app.actions.chat.search", lambda *_: [])
    params = AskChatParams(question="Why is it shared?", mode="chat", source_context="Singleton means one instance per container.")
    events = _events(list(stream_chat(_ctx(client), params)))
    assert events[-1] == ("done", {})
    assert "Source passage being read" in llm.calls[0][2]
    assert "Singleton means one instance" in llm.calls[0][2]
    assert "create_note" in llm.offered_tools[0]
