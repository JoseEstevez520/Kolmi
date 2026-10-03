"""When the daily pass is due, from the class settings.

The host cron wakes the pass every hour with `--if-due`; this decides whether this hour is
one the admin asked for. Times are HH:MM in the class's own time zone.
"""

from __future__ import annotations

from datetime import datetime, time
from typing import Any
from zoneinfo import ZoneInfo

TIMEZONE = "Europe/Madrid"


def is_due(now: datetime, settings: dict[str, Any], last_run: datetime | None) -> bool:
    """Enabled, today is a chosen day, and a chosen time has passed since the last pass.

    `last_run` is when the latest pass started (any status), so each slot runs once and a
    cron that comes late still catches up. Both datetimes must be timezone-aware.
    """
    if not settings.get("pass_enabled", True):
        return False
    tz = ZoneInfo(TIMEZONE)
    local = now.astimezone(tz)
    if local.isoweekday() not in settings.get("pass_days", []):
        return False
    for text in settings.get("pass_times", []):
        hour, minute = map(int, text.split(":"))
        slot = datetime.combine(local.date(), time(hour, minute), tzinfo=tz)
        if slot <= local and (last_run is None or last_run < slot):
            return True
    return False
