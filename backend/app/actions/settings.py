from datetime import datetime, timezone

from fastapi import HTTPException
from pydantic import BaseModel

from ..auth import Context
from ..class_settings import LANGUAGES, SETTINGS_ID, read_settings
from .registry import action


class UpdateSettingsParams(BaseModel):
    class_language: str


@action(
    name="get_settings",
    description="The class settings: the language the AI writes the shared notes and pages in.",
    method="GET",
    path="/settings",
)
def get_settings(ctx: Context, params: None):
    return read_settings(ctx.client)


@action(
    name="update_settings",
    description="Set the class language, the one the AI writes the shared notes and pages in.",
    params=UpdateSettingsParams,
    path="/settings",
    min_role="admin",
)
def update_settings(ctx: Context, params: UpdateSettingsParams):
    # The route checks the role too; the handler checks it again so the future chat, which
    # calls handlers directly, cannot skip it.
    if not (ctx.profile and ctx.profile.get("role") == "admin"):
        raise HTTPException(403, "Admin only")

    code = params.class_language.strip().lower()
    if code not in LANGUAGES:
        supported = ", ".join(LANGUAGES)
        raise HTTPException(422, f"Unsupported language. Use one of: {supported}")

    row = {
        "id": SETTINGS_ID,
        "class_language": code,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        ctx.client.table("settings").upsert(row).execute()
    except Exception as exc:
        raise HTTPException(
            503, "The settings table is missing. Apply the settings migration first."
        ) from exc
    return read_settings(ctx.client)
