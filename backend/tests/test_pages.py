from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException

from app.actions import get_registry, invoke, pages
from app.auth import Context
from tests.fakes import FakeLLM
from tests.test_content import _Query, _Table


class _Client:
    """Tables in memory: nodes, node_versions, ai_log and the class settings."""

    def __init__(self, nodes: list[dict[str, Any]]) -> None:
        self.tables: dict[str, list[dict[str, Any]]] = {
            "nodes": nodes,
            "node_versions": [],
            "ai_log": [],
        }

    def table(self, name: str) -> _Table:
        return _Table(self.tables.setdefault(name, []))


def _nodes() -> list[dict[str, Any]]:
    return [
        {"id": 1, "parent_id": None, "kind": "section", "title": "Unit", "position": 0},
        {
            "id": 2, "parent_id": 1, "kind": "page", "title": "Loops", "position": 0,
            "content_md": "old md", "content_web": "old web",
        },
    ]


def _ctx(client, source="mcp") -> Context:
    profile = {"id": "u1", "role": "admin", "approved": True}
    return Context(user_id="u1", email=None, profile=profile, client=client, source=source)


@pytest.fixture(autouse=True)
def _language(monkeypatch):
    monkeypatch.setattr(pages, "class_language", lambda client: "en")


def _run(client, **kw):
    kw.setdefault("mode", "replace")
    pages.rewrite_page(
        client, node_id=2, markdown="# New", user_id="u1", source="mcp",
        llm=kw.pop("llm", FakeLLM(text_response="# Web")), web_llm=None, **kw,
    )


def _page(client):
    return client.tables["nodes"][1]


def test_replace_writes_the_markdown_as_given_and_keeps_the_old_version():
    client = _Client(_nodes())
    llm = FakeLLM(text_response="web out")

    _run(client, llm=llm)

    assert _page(client)["content_md"] == "# New"
    assert client.tables["node_versions"] == [
        {"node_id": 2, "content_md": "old md", "content_web": "old web"}
    ]
    log = client.tables["ai_log"][0]
    assert log["action"] == "updated"
    assert log["reason"] == "Written from outside the pass (replace)"
    assert log["user_id"] == "u1" and log["source"] == "mcp"
    assert all("New material" not in call[2] for call in llm.calls)


def test_the_source_url_goes_in_the_reason():
    client = _Client(_nodes())

    _run(client, source_url="https://moodle.test/x")

    assert client.tables["ai_log"][0]["reason"].endswith("from https://moodle.test/x")


def test_merge_stores_what_the_notes_agent_writes():
    client = _Client(_nodes())
    llm = FakeLLM(text_response="merged md")

    _run(client, mode="merge", llm=llm)

    assert _page(client)["content_md"] == "merged md"
    first = llm.calls[0]
    assert "# New" in first[2] and "old md" in first[2]


def test_merge_keeps_the_page_when_the_agent_answers_nothing():
    client = _Client(_nodes())

    _run(client, mode="merge", llm=FakeLLM(text_response=""))

    assert _page(client)["content_md"] == "old md"


def test_a_failing_write_is_flagged_and_does_not_raise(monkeypatch):
    client = _Client(_nodes())

    def boom(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(pages, "build_page", boom)
    _run(client)

    assert _page(client)["content_md"] == "old md"
    log = client.tables["ai_log"][0]
    assert log["action"] == "flagged"
    assert log["reason"] == "Could not write the page: boom"
    assert log["user_id"] == "u1" and log["source"] == "mcp"


def test_write_page_answers_queued_without_running_the_job(monkeypatch):
    client = _Client(_nodes())
    started: list[dict[str, Any]] = []
    monkeypatch.setattr(pages, "start_rewrite", lambda c, **kw: started.append(kw))

    result = invoke(
        get_registry()["write_page"], _ctx(client, "chat"),
        {"node_id": 2, "markdown": "# Hi", "mode": "replace"},
    )

    assert result == {"status": "queued", "node_id": 2}
    assert started[0]["user_id"] == "u1" and started[0]["source"] == "chat"
    assert _page(client)["content_md"] == "old md"


def test_a_section_is_refused():
    with pytest.raises(HTTPException) as err:
        invoke(
            get_registry()["write_page"], _ctx(_Client(_nodes())),
            {"node_id": 1, "markdown": "x", "mode": "replace"},
        )
    assert err.value.status_code == 422
    assert "create_node" in err.value.detail


def test_a_missing_node_is_a_404():
    with pytest.raises(HTTPException) as err:
        invoke(
            get_registry()["write_page"], _ctx(_Client(_nodes())),
            {"node_id": 99, "markdown": "x", "mode": "merge"},
        )
    assert err.value.status_code == 404
    assert "list_nodes" in err.value.detail
