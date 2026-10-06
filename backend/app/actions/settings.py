import re
from datetime import datetime, timezone

from fastapi import HTTPException
from pydantic import BaseModel

from ..auth import Context
from ..class_settings import LANGUAGES, SETTINGS_ID, read_settings
from .registry import action


TIME = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
ON_THE_HOUR = re.compile(r"^([01]\d|2[0-3]):00$")


class ScheduleBreak(BaseModel):
    start: str
    end: str
    label: str


class UpdateSettingsParams(BaseModel):
    class_language: str | None = None
    pass_enabled: bool | None = None
    pass_times: list[str] | None = None
    pass_days: list[int] | None = None
    schedule_enabled: bool | None = None
    schedule_days: list[int] | None = None
    schedule_start: str | None = None
    schedule_end: str | None = None
    schedule_breaks: list[ScheduleBreak] | None = None
    schedule_session_minutes: int | None = None
    chat_enabled: bool | None = None
    chat_daily_limit: int | None = None
    signups_need_approval: bool | None = None
    mcp_daily_notes: int | None = None


@action(
    name="get_settings",
    read_only=True,
    tool=True,
    description="The class settings: the AI's language, when its daily pass runs, the class timetable's days, hours and breaks (schedule_days is what a slot's day indexes), the chat's switch and daily cap, whether new sign-ups wait for an admin, and how many notes a student may leave a day through their own AI.",
    method="GET",
    path="/settings",
)
def get_settings(ctx: Context, params: None):
    return read_settings(ctx.client)


@action(
    name="update_settings",
    description="Set the class language, the daily pass's schedule, the class timetable's shape (days, hours, breaks), whether the chat is on and its daily message cap, whether new sign-ups wait for an admin, and how many notes a student may leave a day through their own AI.",
    params=UpdateSettingsParams,
    path="/settings",
    min_role="admin",
)
def update_settings(ctx: Context, params: UpdateSettingsParams):
    current = read_settings(ctx.client)
    row: dict = {"id": SETTINGS_ID, "class_language": current["class_language"]}

    if params.class_language is not None:
        code = params.class_language.strip().lower()
        if code not in LANGUAGES:
            supported = ", ".join(LANGUAGES)
            raise HTTPException(422, f"Unsupported language. Use one of: {supported}")
        row["class_language"] = code

    # The schedule goes in the row only when it is sent, so changing just the language still
    # works before the schedule columns exist.
    if params.pass_times is not None:
        if any(not TIME.match(t) for t in params.pass_times):
            raise HTTPException(422, "Times must be HH:MM, from 00:00 to 23:59")
        # The host cron wakes the pass once an hour, so a time between hours would only run at
        # the next one.
        if any(not ON_THE_HOUR.match(t) for t in params.pass_times):
            raise HTTPException(422, "Times must be on the hour, like 15:00")
        row["pass_times"] = sorted(set(params.pass_times))
    if params.pass_days is not None:
        if any(d < 1 or d > 7 for d in params.pass_days):
            raise HTTPException(422, "Days must be 1 (Monday) to 7 (Sunday)")
        row["pass_days"] = sorted(set(params.pass_days))
    if params.pass_enabled is not None:
        row["pass_enabled"] = params.pass_enabled

    if row.get("pass_enabled", current["pass_enabled"]) and (
        not row.get("pass_times", current["pass_times"])
        or not row.get("pass_days", current["pass_days"])
    ):
        raise HTTPException(422, "Pick at least one time and one day, or turn the pass off")

    if params.schedule_days is not None:
        if not params.schedule_days:
            raise HTTPException(422, "Pick at least one day")
        if any(d < 1 or d > 7 for d in params.schedule_days):
            raise HTTPException(422, "Days must be 1 (Monday) to 7 (Sunday)")
        row["schedule_days"] = sorted(set(params.schedule_days))
    if params.schedule_start is not None:
        if not TIME.match(params.schedule_start):
            raise HTTPException(422, "schedule_start must be HH:MM")
        row["schedule_start"] = params.schedule_start
    if params.schedule_end is not None:
        if not TIME.match(params.schedule_end):
            raise HTTPException(422, "schedule_end must be HH:MM")
        row["schedule_end"] = params.schedule_end
    if params.schedule_breaks is not None:
        for b in params.schedule_breaks:
            if not TIME.match(b.start) or not TIME.match(b.end):
                raise HTTPException(422, "A break's times must be HH:MM")
        row["schedule_breaks"] = [b.model_dump() for b in params.schedule_breaks]
    if params.schedule_session_minutes is not None:
        if params.schedule_session_minutes <= 0:
            raise HTTPException(422, "schedule_session_minutes must be a positive number")
        row["schedule_session_minutes"] = params.schedule_session_minutes
    if params.schedule_enabled is not None:
        row["schedule_enabled"] = params.schedule_enabled

    if params.chat_daily_limit is not None:
        if params.chat_daily_limit <= 0:
            raise HTTPException(422, "chat_daily_limit must be a positive number")
        row["chat_daily_limit"] = params.chat_daily_limit
    if params.chat_enabled is not None:
        row["chat_enabled"] = params.chat_enabled
    if params.signups_need_approval is not None:
        row["signups_need_approval"] = params.signups_need_approval
    if params.mcp_daily_notes is not None:
        if params.mcp_daily_notes <= 0:
            raise HTTPException(422, "mcp_daily_notes must be a positive number")
        row["mcp_daily_notes"] = params.mcp_daily_notes

    row["updated_at"] = datetime.now(timezone.utc).isoformat()
    try:
        ctx.client.table("settings").upsert(row).execute()
    except Exception as exc:
        raise HTTPException(
            503, "The settings table is missing. Apply the settings migration first."
        ) from exc
    return read_settings(ctx.client)
