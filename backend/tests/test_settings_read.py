from __future__ import annotations

from app import class_settings


class _Missing(Exception):
    code = "42703"


def _client_failing(monkeypatch, failures):
    """`_select` raises the given exceptions in turn, then answers a full row."""
    calls = []

    def select(client, columns):
        calls.append(columns)
        if failures:
            raise failures.pop(0)
        return [{"class_language": "es", "chat_enabled": True}]

    monkeypatch.setattr(class_settings, "_select", select)
    return calls


def test_a_dropped_connection_is_asked_again_with_every_column(monkeypatch):
    calls = _client_failing(monkeypatch, [ConnectionError("Server disconnected")])
    assert class_settings.read_settings(object())["chat_enabled"] is True
    assert calls[0] == calls[1] == class_settings._COLUMN_SETS[0]


def test_a_missing_column_falls_back_to_fewer(monkeypatch):
    calls = _client_failing(monkeypatch, [_Missing("column settings.bug_report_daily_limit does not exist")])
    class_settings.read_settings(object())
    assert calls == class_settings._COLUMN_SETS[:2]
