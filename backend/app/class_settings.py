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


def default_language() -> str:
    """`CLASS_LANGUAGE` from the environment, or English when it is not a supported code."""
    code = (get_settings().class_language or "").strip().lower()
    return code if code in LANGUAGES else FALLBACK_LANGUAGE


def language_name(code: str) -> str:
    return LANGUAGES.get(code, LANGUAGES[FALLBACK_LANGUAGE])


def _row(client) -> dict[str, Any] | None:
    try:
        rows = (
            client.table("settings")
            .select("class_language, updated_at")
            .eq("id", SETTINGS_ID)
            .limit(1)
            .execute()
            .data
        )
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
        "languages": [{"code": code, "name": name} for code, name in LANGUAGES.items()],
    }


def class_language(client) -> str:
    return read_settings(client)["class_language"]
