from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from fastapi import HTTPException

from app.actions.settings import UpdateSettingsParams, update_settings
from app.passes.daily import run_daily_pass
from app.passes.schedule import is_due
from tests.fakes import FakeLLM, FakeStore
from tests.test_settings import _ctx, _Table

MADRID = ZoneInfo("Europe/Madrid")
# 2026-10-05 is a Monday.
SETTINGS = {"pass_enabled": True, "pass_times": ["03:00"], "pass_days": [1, 2, 3, 4, 5]}


def at(day: int, hour: int, minute: int = 0, month: int = 10) -> datetime:
    return datetime(2026, month, day, hour, minute, tzinfo=MADRID)


def test_due_once_the_time_has_passed():
    assert is_due(at(5, 3), SETTINGS, None)
    assert is_due(at(5, 4), SETTINGS, at(4, 3))  # last pass was yesterday


def test_not_due_before_the_time():
    assert not is_due(at(5, 2, 59), SETTINGS, at(4, 3))


def test_not_due_twice_for_the_same_slot():
    assert not is_due(at(5, 4), SETTINGS, at(5, 3, 1))


def test_a_late_cron_still_catches_up():
    assert is_due(at(5, 4), {**SETTINGS, "pass_times": ["03:30"]}, at(4, 3, 30))


def test_not_due_on_other_days_or_when_off():
    assert not is_due(at(10, 4), SETTINGS, None)  # Saturday
    assert not is_due(at(5, 4), {**SETTINGS, "pass_enabled": False}, None)


def test_several_times_a_day():
    two = {**SETTINGS, "pass_times": ["03:00", "15:00"]}
    assert not is_due(at(5, 16), two, at(5, 15, 5))
    assert is_due(at(5, 16), two, at(5, 3, 5))


def test_utc_input_is_read_in_madrid():
    # 01:30 UTC on a winter day is 02:30 in Madrid: not yet 03:00.
    assert not is_due(datetime(2026, 1, 12, 1, 30, tzinfo=ZoneInfo("UTC")), SETTINGS, None)
    assert is_due(datetime(2026, 1, 12, 2, 30, tzinfo=ZoneInfo("UTC")), SETTINGS, None)


def test_dst_spring_forward():
    # 2026-03-29 (Sunday): 02:00 jumps to 03:00. A 02:30 slot does not exist; it is due at 03:00.
    sunday = {**SETTINGS, "pass_days": [7], "pass_times": ["02:30"]}
    assert not is_due(at(29, 1, 59, month=3), sunday, None)
    assert is_due(at(29, 3, 0, month=3), sunday, None)


def test_dst_fall_back_runs_once():
    # 2026-10-25 (Sunday): 03:00 goes back to 02:00, so 02:30 happens twice.
    sunday = {**SETTINGS, "pass_days": [7], "pass_times": ["02:30"]}
    first = datetime(2026, 10, 25, 0, 45, tzinfo=ZoneInfo("UTC"))  # 02:45 CEST
    again = datetime(2026, 10, 25, 1, 45, tzinfo=ZoneInfo("UTC"))  # 02:45 CET
    assert is_due(first, sunday, None)
    assert not is_due(again, sunday, first)


def test_if_due_skips_without_asking_the_model():
    store = FakeStore()
    store.settings = {**SETTINGS, "pass_enabled": False}
    llm = FakeLLM()

    summary = run_daily_pass(store=store, llm=llm, if_due=True)

    assert summary["status"] == "not-due"
    assert llm.calls == []


def test_if_due_runs_when_due(monkeypatch):
    monkeypatch.setattr("app.passes.daily.is_due", lambda *a: True)
    summary = run_daily_pass(store=FakeStore(), llm=FakeLLM(), if_due=True)
    assert summary["status"] == "empty"


# -- the admin saving the schedule -----------------------------------------------------


def _save(**fields):
    table = _Table()
    settings = update_settings(_ctx(table, role="admin"), UpdateSettingsParams(**fields))
    return table, settings


def test_saving_the_schedule():
    table, settings = _save(pass_times=["15:00", "03:00", "03:00"], pass_days=[5, 1])
    assert table.rows[0]["pass_times"] == ["03:00", "15:00"]
    assert table.rows[0]["pass_days"] == [1, 5]


@pytest.mark.parametrize(
    "fields",
    [
        {"pass_times": ["3am"]},
        {"pass_times": ["24:00"]},
        {"pass_times": ["15:30"]},
        {"pass_days": [0]},
        {"pass_days": [8]},
        {"pass_times": []},
        {"pass_days": []},
    ],
)
def test_a_bad_schedule_is_refused(fields):
    with pytest.raises(HTTPException) as exc:
        _save(**fields)
    assert exc.value.status_code == 422


def test_an_empty_schedule_is_fine_when_off():
    table, _ = _save(pass_enabled=False, pass_times=[])
    assert table.rows[0]["pass_enabled"] is False


def test_language_alone_leaves_the_schedule_columns_out():
    table, _ = _save(class_language="es")
    assert "pass_times" not in table.rows[0]
