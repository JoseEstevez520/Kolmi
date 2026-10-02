from __future__ import annotations

import pytest

from app.passes.daily import run_daily_pass
from tests.fakes import FakeLLM, FakeStore


def _note(note_id: int = 1) -> dict:
    return {
        "id": note_id,
        "content": "git commit --amend fixes the last commit",
        "node_id": None,
        "status": "pending",
    }


def _section() -> dict:
    return {
        "id": 10,
        "parent_id": None,
        "kind": "section",
        "title": "Tools",
        "description": "",
    }


def test_creates_a_page_from_a_new_note():
    store = FakeStore(notes=[_note()], nodes=[_section()])
    llm = FakeLLM(
        json_response={
            "batches": [
                {
                    "note_ids": [1],
                    "action": "create",
                    "new_page": {"parent_id": 10, "title": "Git", "description": ""},
                    "summary": "How to amend the last commit.",
                    "reason": "new topic",
                }
            ],
            "discarded": [],
        },
        text_response="# Git\n\nUse `git commit --amend`.",
    )

    summary = run_daily_pass(store=store, llm=llm)

    assert summary["status"] == "done"
    assert summary["created"] == 1
    assert summary["notes"] == 1
    assert store.pending_notes() == []

    page = next(iter(store._pages.values()))
    assert page["content_md"].startswith("# Git")
    assert page["content_web"] == ""
    assert store.versions == []
    assert [entry["action"] for entry in store.logs] == ["created"]


def test_updates_a_page_and_saves_the_previous_version():
    store = FakeStore(
        notes=[_note()],
        nodes=[_section()],
        pages=[{"id": 20, "title": "Git", "content_md": "old", "content_web": ""}],
    )
    llm = FakeLLM(
        json_response={
            "batches": [
                {
                    "note_ids": [1],
                    "action": "update",
                    "node_id": 20,
                    "summary": "Add amend.",
                    "reason": "fits the Git page",
                }
            ],
            "discarded": [],
        },
        text_response="old\n\n## Amend\n\nUse `--amend`.",
    )

    summary = run_daily_pass(store=store, llm=llm)

    assert summary["updated"] == 1
    assert store.versions == [
        {"node_id": 20, "content_md": "old", "content_web": ""}
    ]
    assert store.page(20)["content_md"].startswith("old")
    assert [entry["action"] for entry in store.logs] == ["updated"]


def test_discards_a_note():
    store = FakeStore(notes=[_note()], nodes=[_section()])
    llm = FakeLLM(
        json_response={
            "batches": [],
            "discarded": [{"note_id": 1, "reason": "already covered"}],
        }
    )

    summary = run_daily_pass(store=store, llm=llm)

    assert summary["discarded"] == 1
    assert store._notes[1]["status"] == "discarded"
    assert [entry["action"] for entry in store.logs] == ["discarded"]


def test_dry_run_writes_nothing():
    store = FakeStore(notes=[_note()], nodes=[_section()])
    llm = FakeLLM(
        json_response={
            "batches": [
                {
                    "note_ids": [1],
                    "action": "create",
                    "new_page": {"parent_id": 10, "title": "Git", "description": ""},
                    "summary": "How to amend.",
                    "reason": "new",
                }
            ],
            "discarded": [],
        }
    )

    summary = run_daily_pass(store=store, llm=llm, dry_run=True)

    assert summary["status"] == "dry-run"
    assert summary["batches"][0]["new_page"]["title"] == "Git"
    assert store.passes == {}
    assert store.logs == []
    assert store.pending_notes() != []
    assert len(llm.calls) == 1  # only the gatekeeper ran


def test_skips_when_another_pass_is_running():
    store = FakeStore(notes=[_note()], nodes=[_section()])
    store.passes[1] = {"id": 1, "status": "running", "model": "fake"}
    llm = FakeLLM()

    summary = run_daily_pass(store=store, llm=llm)

    assert summary["status"] == "skipped"
    assert llm.calls == []


def test_returns_empty_when_there_are_no_notes():
    store = FakeStore(nodes=[_section()])
    llm = FakeLLM()

    summary = run_daily_pass(store=store, llm=llm)

    assert summary["status"] == "empty"
    assert llm.calls == []


def test_flags_a_note_the_gatekeeper_did_not_review():
    store = FakeStore(notes=[_note()], nodes=[_section()])
    llm = FakeLLM(json_response={"batches": [], "discarded": []})

    summary = run_daily_pass(store=store, llm=llm)

    assert summary["unreviewed"] == [1]
    assert store._notes[1]["status"] == "pending"
    assert [entry["action"] for entry in store.logs] == ["flagged"]


def test_marks_the_pass_failed_when_the_model_breaks():
    class BrokenLLM(FakeLLM):
        def complete_json(self, system, user):
            raise RuntimeError("boom")

    store = FakeStore(notes=[_note()], nodes=[_section()])

    with pytest.raises(RuntimeError):
        run_daily_pass(store=store, llm=BrokenLLM())

    assert store.passes[1]["status"] == "failed"
    assert store.passes[1]["error"] == "boom"
