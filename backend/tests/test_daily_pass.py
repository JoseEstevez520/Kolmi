from __future__ import annotations

import pytest

from app.passes.daily import (
    GIVEN_UP_REASON,
    MAX_SKIPPED_PASSES,
    UNREVIEWED_REASON,
    run_daily_pass,
)
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


def test_the_notes_agent_decisions_stay_out_of_the_page_and_in_the_stats():
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
        text_response="# Git\n\nUse `git commit --amend`.\n---decisions---\nLeft out the link: it was a duplicate.",
    )

    summary = run_daily_pass(store=store, llm=llm)

    page = next(iter(store._pages.values()))
    assert page["content_md"] == "# Git\n\nUse `git commit --amend`."
    assert summary["pages"][0]["decisions"] == "Left out the link: it was a duplicate."


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


def test_a_note_that_adds_nothing_is_discarded_with_its_reason():
    page = {**_section(), "id": 20, "parent_id": 10, "kind": "page", "title": "Git"}
    store = FakeStore(
        notes=[_note()],
        nodes=[_section(), {**page, "content_md": "Fix the last commit with `--amend`."}],
        pages=[{"id": 20, "title": "Git", "content_md": "Fix it with `--amend`.", "content_web": ""}],
    )
    reason = "repeats page 20: --amend fixes the last commit"
    llm = FakeLLM(json_response={"batches": [], "discarded": [{"note_id": 1, "reason": reason}]})

    summary = run_daily_pass(store=store, llm=llm)

    assert summary["discarded"] == 1
    assert store._notes[1]["status"] == "discarded"
    assert store.logs == [
        {"pass_id": 1, "note_id": 1, "node_id": None, "action": "discarded", "reason": reason}
    ]
    # Only the gatekeeper ran: no notes, no web, and the page is as it was.
    assert [kind for kind, *_ in llm.calls] == ["tools"]
    assert store.versions == []
    assert "adds nothing" in llm.calls[0][1]


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
    assert summary["given_up"] == []
    assert store._notes[1]["status"] == "pending"
    assert [entry["action"] for entry in store.logs] == ["flagged"]


def _skip_everything() -> FakeLLM:
    return FakeLLM(json_response={"batches": [], "discarded": []})


def test_retries_a_skipped_note_and_discards_it_after_the_limit():
    store = FakeStore(notes=[_note()], nodes=[_section()])

    for _ in range(MAX_SKIPPED_PASSES - 1):
        summary = run_daily_pass(store=store, llm=_skip_everything())
        assert summary["given_up"] == []
        assert store._notes[1]["status"] == "pending"

    summary = run_daily_pass(store=store, llm=_skip_everything())

    assert summary["given_up"] == [1]
    assert summary["discarded"] == 1
    assert store._notes[1]["status"] == "discarded"
    assert [(e["action"], e["reason"]) for e in store.logs] == [
        *[("flagged", UNREVIEWED_REASON)] * (MAX_SKIPPED_PASSES - 1),
        ("discarded", GIVEN_UP_REASON),
    ]

    # Gone from the queue: the next pass has nothing to do.
    assert run_daily_pass(store=store, llm=_skip_everything())["status"] == "empty"


def test_only_counts_skips_of_the_same_note():
    store = FakeStore(notes=[_note(1), _note(2)], nodes=[_section()])
    for pass_id in range(1, MAX_SKIPPED_PASSES):
        store.log(
            pass_id=pass_id,
            note_id=1,
            node_id=None,
            action="flagged",
            reason=UNREVIEWED_REASON,
        )
    # A flag for another reason does not count.
    store.log(pass_id=1, note_id=2, node_id=None, action="flagged", reason="other")

    summary = run_daily_pass(store=store, llm=_skip_everything())

    assert summary["unreviewed"] == [1, 2]
    assert summary["given_up"] == [1]
    assert store._notes[1]["status"] == "discarded"
    assert store._notes[2]["status"] == "pending"


def test_dry_run_reports_but_does_not_apply_the_discard_rule():
    store = FakeStore(notes=[_note()], nodes=[_section()])
    for pass_id in range(1, MAX_SKIPPED_PASSES):
        store.log(
            pass_id=pass_id,
            note_id=1,
            node_id=None,
            action="flagged",
            reason=UNREVIEWED_REASON,
        )
    logs_before = list(store.logs)

    summary = run_daily_pass(store=store, llm=_skip_everything(), dry_run=True)

    assert summary["status"] == "dry-run"
    assert summary["would_give_up"] == [1]
    assert store._notes[1]["status"] == "pending"
    assert store.logs == logs_before
    assert store.passes == {}


def test_marks_the_pass_failed_when_the_model_breaks():
    class BrokenLLM(FakeLLM):
        def complete_json(self, system, user):
            raise RuntimeError("boom")

    store = FakeStore(notes=[_note()], nodes=[_section()])

    with pytest.raises(RuntimeError):
        run_daily_pass(store=store, llm=BrokenLLM(tool_error=RuntimeError("no tools")))

    assert store.passes[1]["status"] == "failed"
    assert store.passes[1]["error"] == "boom"


def _file(file_id: int = 5) -> dict:
    return {"id": file_id, "note_id": 1, "name": "slides.pdf", "size": 1000, "kind": "pdf"}


def test_a_note_of_only_files_attaches_them_without_writing_the_page():
    note = {**_note(), "content": "", "files": [_file()]}
    store = FakeStore(notes=[note], nodes=[_section()])
    llm = FakeLLM(
        json_response={
            "batches": [
                {
                    "note_ids": [1],
                    "action": "create",
                    "new_page": {"parent_id": 10, "title": "Slides", "description": ""},
                    "summary": "",
                    "file_ids": [5],
                }
            ],
            "discarded": [],
        },
        text_response="should never be asked for",
    )

    summary = run_daily_pass(store=store, llm=llm)

    assert summary["status"] == "done"
    assert store.attached == [{"file_id": 5, "node_id": 1}]
    assert next(iter(store._pages.values()))["content_md"] == ""
    assert store.pending_notes() == []


def test_a_note_with_neither_text_nor_files_is_left_out_of_the_pass():
    store = FakeStore(notes=[{**_note(), "content": "  \n"}], nodes=[_section()])

    assert run_daily_pass(store=store, llm=FakeLLM())["status"] == "empty"
