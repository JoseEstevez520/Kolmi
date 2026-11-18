from __future__ import annotations

from types import SimpleNamespace

from app.actions import get_registry, invoke
from app.actions.passes import failure_reason
from app.auth import Context

DEEPSEEK_402 = (
    "Error code: 402 - {'error': {'message': 'Insufficient Balance (request_id: x)', "
    "'type': 'insufficient_balance_error', 'param': None, 'code': 'invalid_request_error'}}"
)


class _Query:
    def __init__(self, rows):
        self.rows, self.eqs, self.count = rows, [], False

    def select(self, *_a, count=None):
        self.count = bool(count)
        return self

    def eq(self, column, value):
        self.eqs.append((column, value))
        return self

    def order(self, column, desc=False):
        self.rows = sorted(self.rows, key=lambda r: r[column], reverse=desc)
        return self

    def limit(self, n):
        self.rows = self.rows[:n]
        return self

    def execute(self):
        hit = [r for r in self.rows if all(r.get(c) == v for c, v in self.eqs)]
        return SimpleNamespace(data=hit, count=len(hit) if self.count else None)


class _Client:
    def __init__(self, passes, notes=()):
        self.tables = {"ai_passes": list(passes), "notes": list(notes)}

    def table(self, name):
        return _Query(self.tables[name])


def _pass(pass_id, status, day, error=None):
    return {"id": pass_id, "status": status, "error": error, "started_at": f"2026-11-{day:02d}T15:00:00+00:00"}


def _health(client):
    ctx = Context(user_id="u1", email=None, profile={"id": "u1", "role": "admin", "approved": True}, client=client)
    return invoke(get_registry()["pass_health"], ctx, {})


def test_failing_since_the_first_of_the_failures_in_a_row():
    client = _Client(
        [_pass(1, "done", 2), _pass(2, "failed", 3, DEEPSEEK_402), _pass(3, "failed", 4, DEEPSEEK_402)],
        [{"id": 1, "status": "pending"}, {"id": 2, "status": "pending"}, {"id": 3, "status": "processed"}],
    )
    assert _health(client) == {
        "status": "failing",
        "since": "2026-11-03T15:00:00+00:00",
        "failed": 2,
        "reason": "credit",
        "error": DEEPSEEK_402,
        "pending": 2,
    }


def test_a_pass_that_worked_clears_it_and_a_running_one_does_not():
    assert _health(_Client([_pass(1, "failed", 3, "boom"), _pass(2, "done", 4)])) == {"status": "ok"}
    assert _health(_Client([])) == {"status": "ok"}
    running = _Client([_pass(1, "failed", 3, "boom"), _pass(2, "running", 4)])
    assert _health(running)["since"] == "2026-11-03T15:00:00+00:00"


def test_the_error_is_read_in_plain_words():
    assert failure_reason(DEEPSEEK_402) == "credit"
    assert failure_reason("Error code: 429 - {'error': {'code': 'insufficient_quota'}}") == "credit"
    assert failure_reason("Error code: 429 - Rate limit reached") == "quota"
    assert failure_reason("Error code: 401 - Incorrect API key provided") == "auth"
    assert failure_reason("Connection reset by peer") == "other"
    assert failure_reason(None) == "other"
