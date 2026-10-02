from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app import class_settings
from app.actions.settings import UpdateSettingsParams, get_settings, update_settings
from app.agents import openui
from app.auth import Context
from app.passes.daily import run_daily_pass
from tests.fakes import FakeLLM, FakeStore


class _Query:
    def __init__(self, table: _Table, op: str, data: dict[str, Any] | None = None) -> None:
        self.table = table
        self.op = op
        self.data = data

    def eq(self, _column: str, _value: Any) -> _Query:
        return self

    def limit(self, _n: int) -> _Query:
        return self

    def execute(self) -> Any:
        if self.table.missing:
            raise RuntimeError('relation "public.settings" does not exist')
        if self.op == "upsert":
            self.table.rows = [dict(self.data)]
        return SimpleNamespace(data=[dict(r) for r in self.table.rows])


class _Table:
    def __init__(self, rows: list[dict[str, Any]] | None = None, missing: bool = False) -> None:
        self.rows = list(rows or [])
        self.missing = missing

    def select(self, _columns: str) -> _Query:
        return _Query(self, "select")

    def upsert(self, row: dict[str, Any]) -> _Query:
        return _Query(self, "upsert", row)


class _Client:
    def __init__(self, table: _Table) -> None:
        self.settings = table

    def table(self, name: str) -> _Table:
        assert name == "settings"
        return self.settings


def _ctx(table: _Table, role: str = "student") -> Context:
    profile = {"id": "u1", "name": "Ana", "role": role, "approved": True}
    return Context(user_id="u1", email=None, profile=profile, client=_Client(table))


@pytest.fixture
def env_language(monkeypatch):
    """Set CLASS_LANGUAGE as the settings would read it from the environment."""

    def set_language(code: str) -> None:
        monkeypatch.setattr(
            class_settings, "get_settings", lambda: SimpleNamespace(class_language=code)
        )

    set_language("en")
    return set_language


# -- reading the class language ------------------------------------------------------


def test_the_stored_row_wins_over_the_environment(env_language):
    env_language("en")
    table = _Table(rows=[{"class_language": "es", "updated_at": "2026-10-01T00:00:00Z"}])

    settings = get_settings(_ctx(table), None)

    assert settings["class_language"] == "es"
    assert {"code": "es", "name": "Spanish"} in settings["languages"]


def test_without_a_row_the_environment_decides(env_language):
    env_language("es")

    assert get_settings(_ctx(_Table()), None)["class_language"] == "es"


def test_without_the_table_the_environment_decides(env_language):
    env_language("es")

    settings = get_settings(_ctx(_Table(missing=True)), None)

    assert settings["class_language"] == "es"
    assert settings["updated_at"] is None


def test_an_unsupported_environment_value_falls_back_to_english(env_language):
    env_language("xx")

    assert class_settings.class_language(_Client(_Table(missing=True))) == "en"


# -- changing it ---------------------------------------------------------------------


def test_an_admin_sets_the_class_language(env_language):
    table = _Table()

    settings = update_settings(
        _ctx(table, role="admin"), UpdateSettingsParams(class_language="ES")
    )

    assert settings["class_language"] == "es"
    assert table.rows[0]["id"] == 1
    assert table.rows[0]["class_language"] == "es"


def test_a_student_cannot_set_it(env_language):
    table = _Table()

    with pytest.raises(HTTPException) as exc:
        update_settings(_ctx(table), UpdateSettingsParams(class_language="es"))

    assert exc.value.status_code == 403
    assert table.rows == []


def test_the_route_is_admin_only():
    from app.actions import get_registry

    registry = get_registry()
    assert registry["update_settings"].min_role == "admin"
    assert registry["get_settings"].min_role == "student"


def test_an_unsupported_language_is_refused(env_language):
    table = _Table()

    with pytest.raises(HTTPException) as exc:
        update_settings(_ctx(table, role="admin"), UpdateSettingsParams(class_language="fr"))

    assert exc.value.status_code == 422
    assert table.rows == []


def test_the_language_is_required():
    with pytest.raises(ValidationError):
        UpdateSettingsParams.model_validate({})


def test_saving_without_the_table_says_what_is_missing(env_language):
    with pytest.raises(HTTPException) as exc:
        update_settings(
            _ctx(_Table(missing=True), role="admin"), UpdateSettingsParams(class_language="es")
        )

    assert exc.value.status_code == 503


# -- the pass writes in it -----------------------------------------------------------


def _note() -> dict:
    return {
        "id": 1,
        "content": "git commit --amend arregla el último commit",
        "node_id": None,
        "status": "pending",
    }


def _plan() -> dict:
    return {
        "batches": [
            {
                "note_ids": [1],
                "action": "create",
                "new_page": {"parent_id": None, "title": "Git", "description": ""},
                "summary": "How to amend the last commit.",
                "reason": "new topic",
            }
        ],
        "discarded": [],
    }


def test_the_pass_writes_in_the_language_it_is_given():
    store = FakeStore(notes=[_note()])
    llm = FakeLLM(json_response=_plan(), text_response="# Git\n\nUsa `--amend`.")

    summary = run_daily_pass(store=store, llm=llm, language="es")

    assert summary["language"] == "es"
    # The gatekeeper, the Markdown, then the page as OpenUI Lang (not a page here).
    (_, gatekeeper, _), (_, notes, _), (_, _, page_brief) = llm.calls
    assert "in Spanish" in gatekeeper
    assert page_brief.startswith("Write the whole page in Spanish.")
    assert "in Spanish" in notes
    assert "English" not in notes


def test_the_pass_reads_the_class_language_from_the_store():
    store = FakeStore(notes=[_note()], language="es")
    llm = FakeLLM(json_response=_plan(), text_response="# Git")

    summary = run_daily_pass(store=store, llm=llm)

    assert summary["language"] == "es"
    assert all("in Spanish" in system + user for _, system, user in llm.calls)


def test_the_web_agent_is_told_the_language_in_its_brief():
    store = FakeStore(notes=[_note()])
    llm = FakeLLM(json_response=_plan(), text_response="Usa `--amend`.")
    web = FakeLLM(text_response='root = Page([t])\nt = Text("Usa --amend.")')

    run_daily_pass(store=store, llm=llm, web_llm=web, language="es")

    (_, system, brief), = web.calls
    assert system == openui.full_prompt()
    assert brief.startswith("Write the whole page in Spanish.")


def test_the_dry_run_asks_the_gatekeeper_in_the_language():
    store = FakeStore(notes=[_note()])
    llm = FakeLLM(json_response=_plan())

    summary = run_daily_pass(store=store, llm=llm, language="es", dry_run=True)

    assert summary["language"] == "es"
    assert "in Spanish" in llm.calls[0][1]
