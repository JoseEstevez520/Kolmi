"""The class's own settings: one row in `settings`, read by the API and the daily pass.

Until the `settings` table exists (or while it has no row), every value falls back to the
environment, so a fresh instance works before an admin touches anything.
"""

from __future__ import annotations

import logging
from typing import Any

from .config import get_settings

log = logging.getLogger(__name__)

# The languages the AI can write the shared notes and pages in, by code. The one place to
# add a language: the API validates against it and the prompts name the language from it.
LANGUAGES: dict[str, str] = {
    "en": "English",
    "es": "Spanish",
}

FALLBACK_LANGUAGE = "en"
SETTINGS_ID = 1

# The pass's schedule, until the admin sets one (and while the columns are not there yet):
# every day at 03:00, Europe/Madrid. Days are ISO weekdays, 1 Monday to 7 Sunday.
DEFAULT_PASS = {
    "pass_enabled": True,
    "pass_times": ["03:00"],
    "pass_days": [1, 2, 3, 4, 5, 6, 7],
}
PASS_COLUMNS = ", ".join(DEFAULT_PASS)

# The class's own weekly timetable (not the pass's), until the admin sets one.
DEFAULT_SCHEDULE = {
    "schedule_enabled": False,
    "schedule_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    "schedule_start": "08:10",
    "schedule_end": "15:20",
    "schedule_breaks": [],
    # A real session's length in minutes: dragging a slot in Admin snaps to a multiple of it.
    "schedule_session_minutes": 50,
}
SCHEDULE_COLUMNS = ", ".join(DEFAULT_SCHEDULE)


def default_language() -> str:
    """`CLASS_LANGUAGE` from the environment, or English when it is not a supported code."""
    code = (get_settings().class_language or "").strip().lower()
    return code if code in LANGUAGES else FALLBACK_LANGUAGE


def language_name(code: str) -> str:
    return LANGUAGES.get(code, LANGUAGES[FALLBACK_LANGUAGE])


def _select(client, columns: str) -> list[dict[str, Any]]:
    return (
        client.table("settings").select(columns).eq("id", SETTINGS_ID).limit(1).execute().data
    )


def _row(client) -> dict[str, Any] | None:
    try:
        try:
            rows = _select(
                client, f"class_language, updated_at, {PASS_COLUMNS}, {SCHEDULE_COLUMNS}"
            )
        except Exception:  # the pass or timetable columns are not there yet
            try:
                rows = _select(client, f"class_language, updated_at, {PASS_COLUMNS}")
            except Exception:
                rows = _select(client, "class_language, updated_at")
    except Exception as exc:  # the table is not there yet, or Supabase is unreachable
        log.warning("could not read the settings row, using the environment: %s", exc)
        return None
    return rows[0] if rows else None


def read_settings(client) -> dict[str, Any]:
    """The class settings: the stored row when there is one, the environment otherwise."""
    row = _row(client)
    stored = (row or {}).get("class_language")
    language = stored if stored in LANGUAGES else default_language()
    return {
        "class_language": language,
        "updated_at": (row or {}).get("updated_at"),
        **{key: (row or {}).get(key, default) for key, default in DEFAULT_PASS.items()},
        **{key: (row or {}).get(key, default) for key, default in DEFAULT_SCHEDULE.items()},
        "timezone": "Europe/Madrid",
        "languages": [{"code": code, "name": name} for code, name in LANGUAGES.items()],
    }


def class_language(client) -> str:
    return read_settings(client)["class_language"]
