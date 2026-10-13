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
    def __init__(self, status=201, open_issues=None, list_status=200):
        self.status, self.calls, self.gets = status, [], []
        self.open_issues, self.list_status = open_issues, list_status

    def get(self, url, **kw):
        self.gets.append((url, kw))
        if self.open_issues is None:
            raise RuntimeError("network down")
        return SimpleNamespace(status_code=self.list_status, json=lambda: self.open_issues)

    def post(self, url, **kw):
        self.calls.append((url, kw))
        return SimpleNamespace(
            status_code=self.status, json=lambda: {"html_url": "https://github.com/o/r/issues/7"}
        )


OPEN = [
    {"number": 3, "title": "Saving fails", "html_url": "https://github.com/o/r/issues/3"},
    {"number": 4, "title": "A pull request", "html_url": "x", "pull_request": {}},
]


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
    assert kw["json"]["labels"] == ["bug-report", "severity:high", "bug"]
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


def test_a_duplicate_comments_on_the_existing_issue():
    client, http = _Client(), _Http(open_issues=OPEN)
    _report(client)
    row = _process(client, {**GENUINE, "duplicate_of": 3}, http)
    assert row["status"] == "issue" and row["issue_url"] == "https://github.com/o/r/issues/3"
    assert row["verdict"]["duplicate_of"] == 3
    url, kw = http.calls[0]
    assert url == "https://api.github.com/repos/o/r/issues/3/comments" and len(http.calls) == 1
    assert kw["json"]["body"].startswith("Another person reported this: Save fails.")


def test_the_judge_only_sees_issues_not_pull_requests_and_an_unknown_number_is_ignored():
    seen = []
    llm = FakeLLM(json_response={**GENUINE, "duplicate_of": 99})
    orig = llm.complete_json
    llm.complete_json = lambda system, user: (seen.append(user), orig(system, user))[1]
    client, http = _Client(), _Http(open_issues=OPEN)
    _report(client)
    bugs.process_report(client, 1, title="T", body="B", page_path=None, llm=llm, http=http)
    assert "#3: Saving fails" in seen[0] and "pull request" not in seen[0]
    assert client.reports[0]["verdict"]["duplicate_of"] is None
    assert http.calls[0][0].endswith("/repos/o/r/issues")


def test_if_the_candidates_cannot_be_fetched_it_files_normally():
    for http in (_Http(), _Http(open_issues=[], list_status=403)):
        client = _Client()
        _report(client)
        row = _process(client, GENUINE, http)
        assert row["status"] == "issue" and http.calls[0][0].endswith("/repos/o/r/issues")


def test_the_candidates_are_capped():
    many = [{"number": n, "title": f"T{n}", "html_url": "u"} for n in range(1, 50)]
    assert len(bugs.open_issues(_Http(open_issues=many))) == bugs.MAX_CANDIDATES


def _admin_client():
    return _Client([
        {"id": 1, "user_id": "u1", "title": "A", "body": "raw A", "status": "discarded", "verdict": {"reason": "Joke"}, "profiles": {"name": "Ana"}},
        {"id": 2, "user_id": "u2", "title": "B", "body": "raw B", "status": "pending",
         "verdict": {**GENUINE}, "profiles": [{"name": "Bo"}]},
        {"id": 3, "user_id": "u2", "title": "C", "body": "raw C", "status": "issue", "issue_url": "u"},
    ])


def test_only_an_admin_lists_files_or_discards():
    client = _admin_client()
    for name, args in (("list_bug_reports", None), ("file_bug_report", {"id": 2}), ("discard_bug_report", {"id": 2})):
        with pytest.raises(HTTPException) as err:
            invoke(get_registry()[name], _ctx(client), args)
        assert err.value.status_code == 403


def test_an_admin_lists_every_report_with_its_author():
    out = invoke(get_registry()["list_bug_reports"], _ctx(_admin_client(), "admin"), None)
    assert [(r["id"], r["author"], r["status"]) for r in out] == [(1, "Ana", "discarded"), (2, "Bo", "pending"), (3, None, "issue")]
    assert out[0]["reason"] == "Joke"


def test_an_admin_files_a_pending_report_and_a_discarded_one_through_the_judge(monkeypatch):
    http = _Http(open_issues=[])
    monkeypatch.setattr(bugs, "open_issues", lambda h=None: [])
    monkeypatch.setattr(bugs, "get_llm", lambda: FakeLLM(json_response={**GENUINE, "title": "Clean", "body": "Clean body"}))
    monkeypatch.setattr(bugs, "create_issue", lambda v, p, h=None, environment=None: http.calls.append(v.title) or "https://github.com/o/r/issues/9")
    client = _admin_client()
    admin = _ctx(client, "admin")
    out = invoke(get_registry()["file_bug_report"], admin, {"id": 2})
    assert out["issue_url"].endswith("/9") and client.reports[1]["status"] == "issue"
    invoke(get_registry()["file_bug_report"], admin, {"id": 1})
    assert http.calls == ["Save fails", "Clean"]
    assert client.reports[0]["status"] == "issue"
    with pytest.raises(HTTPException) as err:
        invoke(get_registry()["file_bug_report"], admin, {"id": 3})
    assert err.value.status_code == 409


def test_filing_by_hand_needs_github(monkeypatch):
    monkeypatch.setattr(bug_actions, "github_configured", lambda: False)
    with pytest.raises(HTTPException) as err:
        invoke(get_registry()["file_bug_report"], _ctx(_admin_client(), "admin"), {"id": 2})
    assert err.value.status_code == 409


def test_an_admin_discards_with_a_reason_but_not_a_filed_report():
    client = _admin_client()
    admin = _ctx(client, "admin")
    invoke(get_registry()["discard_bug_report"], admin, {"id": 2, "reason": "Not ours"})
    assert client.reports[1]["status"] == "discarded" and client.reports[1]["verdict"]["reason"] == "Not ours"
    assert client.reports[1]["verdict"]["severity"] == "high"
    with pytest.raises(HTTPException) as err:
        invoke(get_registry()["discard_bug_report"], admin, {"id": 3})
    assert err.value.status_code == 409


def test_the_environment_is_stored_on_one_line_and_reaches_the_judge_and_the_issue():
    client, http, seen = _Client(), _Http(), []
    invoke(get_registry()["report_bug"], _ctx(client), {
        "title": "T", "body": "B", "page_path": "/node/2",
        "environment": "Chrome 130 on Linux,\n390px, dark theme, en",
    })
    assert client.reports[0]["environment"] == "Chrome 130 on Linux, 390px, dark theme, en"
    llm = FakeLLM(json_response=GENUINE)
    orig = llm.complete_json
    llm.complete_json = lambda system, user: (seen.append(user), orig(system, user))[1]
    bugs.process_report(client, 1, title="T", body="B", page_path="/node/2",
                        environment=client.reports[0]["environment"], llm=llm, http=http)
    assert "Environment: Chrome 130 on Linux, 390px, dark theme, en" in seen[0]
    assert "Environment: Chrome 130 on Linux, 390px, dark theme, en" in http.calls[0][1]["json"]["body"]


def test_without_an_environment_the_issue_has_no_such_line():
    client, http = _Client(), _Http()
    _report(client)
    _process(client, GENUINE, http)
    assert "Environment:" not in http.calls[0][1]["json"]["body"]


def test_an_enhancement_is_labelled_so_and_an_unknown_kind_is_not_accepted():
    client, http = _Client(), _Http()
    _report(client)
    _process(client, {**GENUINE, "kind": "enhancement"}, http)
    assert http.calls[0][1]["json"]["labels"][-1] == "enhancement"
    assert bugs.Verdict.model_validate({"genuine": True}).kind == "bug"
    with pytest.raises(Exception):
        bugs.Verdict.model_validate({"genuine": True, "kind": "praise"})


def test_a_duplicate_comment_says_how_many_people_reported_it():
    url = "https://github.com/o/r/issues/3"
    client = _Client([
        {"id": 1, "user_id": "u2", "issue_url": url, "status": "issue"},
        {"id": 2, "user_id": "u3", "issue_url": url, "status": "issue"},
        {"id": 3, "user_id": "u4", "issue_url": "https://github.com/o/r/issues/8", "status": "issue"},
    ])
    http = _Http(open_issues=OPEN)
    invoke(get_registry()["report_bug"], _ctx(client), {"title": "T", "body": "B"})
    bugs.process_report(client, 4, title="T", body="B", page_path=None, llm=FakeLLM(json_response={**GENUINE, "duplicate_of": 3}), http=http)
    body = http.calls[0][1]["json"]["body"]
    assert body.endswith("Reported by 3 people so far.")
    assert "u1" not in body and "@" not in body


def test_the_first_duplicate_has_no_count_and_the_admin_path_counts_too(monkeypatch):
    url = "https://github.com/o/r/issues/3"
    client, http = _Client(), _Http(open_issues=OPEN)
    _report(client)
    _process(client, {**GENUINE, "duplicate_of": 3}, http)
    assert "Reported by" not in http.calls[0][1]["json"]["body"]
    # Another report of the same problem, filed by an admin.
    client.reports.append({"id": 2, "user_id": "u2", "title": "B", "body": "raw", "status": "pending",
                           "verdict": {**GENUINE, "duplicate_of": 3}})
    bugs.file_by_admin(client, client.reports[1], http=http)
    assert http.calls[-1][1]["json"]["body"].endswith("Reported by 2 people so far.")
    assert client.reports[1]["issue_url"] == url
