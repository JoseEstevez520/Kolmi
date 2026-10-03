import re
from datetime import datetime, timezone

from fastapi import HTTPException
from pydantic import BaseModel

from ..auth import Context
from ..class_settings import LANGUAGES, SETTINGS_ID, read_settings
from .registry import action


TIME = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class UpdateSettingsParams(BaseModel):
    class_language: str | None = None
    pass_enabled: bool | None = None
    pass_times: list[str] | None = None
    pass_days: list[int] | None = None


@action(
    name="get_settings",
    description="The class settings: the AI's language and when its daily pass runs.",
    method="GET",
    path="/settings",
)
def get_settings(ctx: Context, params: None):
    return read_settings(ctx.client)


@action(
    name="update_settings",
    description="Set the class language and the daily pass's schedule (on or off, times, weekdays).",
    params=UpdateSettingsParams,
    path="/settings",
    min_role="admin",
)
def update_settings(ctx: Context, params: UpdateSettingsParams):
    # The route checks the role too; the handler checks it again so the future chat, which
    # calls handlers directly, cannot skip it.
    if not (ctx.profile and ctx.profile.get("role") == "admin"):
        raise HTTPException(403, "Admin only")

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

    row["updated_at"] = datetime.now(timezone.utc).isoformat()
    try:
        ctx.client.table("settings").upsert(row).execute()
    except Exception as exc:
        raise HTTPException(
            503, "The settings table is missing. Apply the settings migration first."
        ) from exc
    return read_settings(ctx.client)
