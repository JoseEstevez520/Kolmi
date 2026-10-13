from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException

from app import bugs
from app.actions import bugs as bug_actions
from app.actions import get_registry, invoke
from app.auth import Context
from tests.fakes import FakeLLM


class _Query:
    def __init__(self, rows, op="select", data=None):
        self.rows, self.op, self.data, self.eqs = rows, op, data, []

    def select(self, *_a, **_k): return self
    def eq(self, column, value): self.eqs.append((column, value)); return self
    def gte(self, *_a): return self
    def order(self, *_a, **_k): return self
    def limit(self, _n): return self

    def execute(self):
        if self.op == "insert":
            row = {"id": len(self.rows) + 1, **self.data}
            self.rows.append(row)
            return SimpleNamespace(data=[row], count=None)
        hit = [r for r in self.rows if all(r.get(c) == v for c, v in self.eqs)]
        if self.op == "update":
            for r in hit:
                r.update(self.data)
        return SimpleNamespace(data=[dict(r) for r in hit], count=len(hit))


class _Client:
    def __init__(self, reports=None):
        self.reports: list[dict[str, Any]] = reports if reports is not None else []

    def table(self, name):
        assert name == "bug_reports"
        return _Table(self.reports)


class _Table:
    def __init__(self, rows): self.rows = rows
    def select(self, *_a, **_k): return _Query(self.rows)
    def insert(self, data): return _Query(self.rows, "insert", data)
    def update(self, data): return _Query(self.rows, "update", data)


class _Http:
    def __init__(self, status=201):
        self.status, self.calls = status, []

    def post(self, url, **kw):
        self.calls.append((url, kw))
        return SimpleNamespace(
            status_code=self.status, json=lambda: {"html_url": "https://github.com/o/r/issues/7"}
        )


GENUINE = {"genuine": True, "severity": "high", "title": "Save fails", "body": "Saving a note fails.", "reason": "Clear steps."}
TROLL = {"genuine": False, "severity": "low", "title": "", "body": "", "reason": "A joke, not about the app."}


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setattr(bugs, "get_settings", lambda: SimpleNamespace(github_token="t0k", github_repo="o/r"))
    monkeypatch.setattr(bug_actions, "read_settings", lambda client: {"bug_report_daily_limit": 2})
    monkeypatch.setattr(bug_actions, "start_report", lambda *a, **k: None)


def _ctx(client, role="student"):
    return Context(user_id="u1", email=None, profile={"id": "u1", "role": role, "status": "active"}, client=client)


def _report(client, **kw):
    return invoke(get_registry()["report_bug"], _ctx(client, **kw), {"title": "T", "body": "B", "page_path": "/node/2"})


def _process(client, llm_json, http=None):
    row = client.reports[0]
    bugs.process_report(client, row["id"], title="T", body="B", page_path="/node/2", llm=FakeLLM(json_response=llm_json), http=http)
    return client.reports[0]


def test_a_report_is_kept_at_once_as_pending():
    client = _Client()
    assert _report(client)["status"] == "queued"
    assert client.reports[0]["status"] == "pending" and client.reports[0]["body"] == "B"


def test_a_student_is_capped_and_an_admin_is_not():
    client = _Client([{"id": 1, "user_id": "u1"}, {"id": 2, "user_id": "u1"}])
    with pytest.raises(HTTPException) as err:
        _report(client)
    assert err.value.status_code == 429
    assert _report(client, role="admin")["status"] == "queued"


def test_a_genuine_report_becomes_an_issue_with_its_severity():
    client, http = _Client(), _Http()
    _report(client)
    row = _process(client, GENUINE, http)
    assert row["status"] == "issue"
    assert row["issue_url"] == "https://github.com/o/r/issues/7"
    url, kw = http.calls[0]
    assert url == "https://api.github.com/repos/o/r/issues"
    assert "severity:high" in kw["json"]["labels"]
    assert kw["headers"]["Authorization"] == "Bearer t0k"
    assert row["verdict"]["reason"] == "Clear steps."


def test_a_troll_is_discarded_with_its_reason():
    client, http = _Client(), _Http()
    _report(client)
    row = _process(client, TROLL, http)
    assert row["status"] == "discarded" and row["verdict"]["reason"] == "A joke, not about the app."
    assert http.calls == []


def test_without_a_token_the_verdict_is_kept_and_it_stays_pending(monkeypatch):
    monkeypatch.setattr(bugs, "get_settings", lambda: SimpleNamespace(github_token="", github_repo=""))
    client, http = _Client(), _Http()
    _report(client)
    row = _process(client, GENUINE, http)
    assert row["status"] == "pending" and row["verdict"]["severity"] == "high"
    assert http.calls == [] and not row.get("issue_url")


def test_a_github_failure_marks_it_failed_and_keeps_the_report():
    client = _Client()
    _report(client)
    row = _process(client, GENUINE, _Http(status=403))
    assert row["status"] == "failed" and row["body"] == "B"
    assert row["verdict"]["severity"] == "high"
    assert "t0k" not in str(row["verdict"])


def test_a_model_failure_marks_it_failed():
    client = _Client()
    _report(client)

    class Broken:
        def complete_json(self, *_a): raise RuntimeError("down")

    bugs.process_report(client, 1, title="T", body="B", page_path=None, llm=Broken())
    assert client.reports[0]["status"] == "failed"


def test_my_reports_show_where_each_ended_up():
    client = _Client([
        {"id": 1, "user_id": "u1", "title": "A", "status": "discarded", "verdict": {"reason": "Joke"}},
        {"id": 2, "user_id": "u2", "title": "B", "status": "pending"},
    ])
    out = invoke(get_registry()["my_bug_reports"], _ctx(client), None)
    assert [(r["id"], r["status"], r["reason"]) for r in out] == [(1, "discarded", "Joke")]
