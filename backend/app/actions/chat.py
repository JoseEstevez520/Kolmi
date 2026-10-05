from __future__ import annotations

from datetime import datetime, time
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from pydantic import BaseModel

from ..agents import get_llm, run_chat
from ..auth import Context
from ..class_settings import class_language, read_settings
from ..files import node_files
from ..passes.schedule import TIMEZONE
from .content import LIST_COLUMNS
from .registry import action
from .schedule import _resolve

_DAY_NAMES = {
    "es": {1: "Lunes", 2: "Martes", 3: "Miércoles", 4: "Jueves", 5: "Viernes", 6: "Sábado", 7: "Domingo"},
    "en": {1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 5: "Friday", 6: "Saturday", 7: "Sunday"},
}


def _today_text(language: str, tz: str = TIMEZONE) -> str:
    """Today's weekday and date in the class's timezone, as one line: the model otherwise has no
    notion of "today", so it can't work out what "tomorrow" or "this weekend" means on its own.
    """
    now = datetime.now(ZoneInfo(tz))
    names = _DAY_NAMES.get(language, _DAY_NAMES["en"])
    day = names.get(now.isoweekday(), str(now.isoweekday()))
    return f"{day}, {now.date().isoformat()}"


def _schedule_text(client, settings: dict, language: str) -> str:
    """The class timetable as plain text for the chat's context: each slot's day, hours and
    what it's for, in the same shape list_schedule_events shows an admin. Empty when the class
    hasn't turned the timetable on.
    """
    if not settings.get("schedule_enabled"):
        return ""
    events = client.table("schedule_events").select("*").order("day").execute().data
    if not events:
        return ""
    node_ids = {e["node_id"] for e in events if e.get("node_id") is not None}
    nodes = (
        client.table("nodes").select("id, title, color").in_("id", list(node_ids)).execute().data
        if node_ids
        else []
    )
    nodes_by_id = {n["id"]: n for n in nodes}
    names = _DAY_NAMES.get(language, _DAY_NAMES["en"])
    # `event.day` indexes into the admin's chosen days (ISO weekdays, Monday first), not a
    # weekday number itself: the same shape elastic-ui's Timetable and ScheduleView use.
    week_days = settings.get("schedule_days") or []
    lines = []
    for event in sorted(events, key=lambda e: (e["day"], e["start_time"])):
        resolved = _resolve(event, nodes_by_id)
        iso_day = week_days[resolved["day"]] if 0 <= resolved["day"] < len(week_days) else None
        day = names.get(iso_day, str(resolved["day"]))
        detail = f" ({resolved['detail']})" if resolved.get("detail") else ""
        lines.append(f"- {day} {resolved['start_time']}-{resolved['end_time']}: {resolved['title']}{detail}")
    return "\n".join(lines)


class AskChatParams(BaseModel):
    question: str


def _today_start(tz: str = TIMEZONE) -> str:
    now = datetime.now(ZoneInfo(tz))
    return datetime.combine(now.date(), time.min, tzinfo=now.tzinfo).isoformat()


def _messages_today(client, user_id: str) -> int:
    rows = (
        client.table("chat_messages")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .gte("created_at", _today_start())
        .execute()
    )
    return rows.count or 0


def _read_page(client):
    def read(node_id: int) -> dict[str, Any] | None:
        rows = (
            client.table("nodes")
            .select("id, content_md")
            .eq("id", node_id)
            .limit(1)
            .execute()
            .data
        )
        if not rows:
            return None
        return {**rows[0], "files": node_files(client, node_id)}

    return read


@action(
    name="ask_chat",
    description="Ask the hive a question; it answers from the class's shared content.",
    params=AskChatParams,
    path="/chat",
)
def ask_chat(ctx: Context, params: AskChatParams):
    settings = read_settings(ctx.client)
    if not settings.get("chat_enabled"):
        raise HTTPException(403, "The chat is off for this class")

    limit = settings.get("chat_daily_limit", 20)
    if _messages_today(ctx.client, ctx.user_id) >= limit:
        raise HTTPException(429, "You've reached today's limit for the chat")

    question = params.question.strip()
    if not question:
        raise HTTPException(422, "Ask something first")

    nodes = ctx.client.table("nodes").select(LIST_COLUMNS).order("position").execute().data
    language = class_language(ctx.client)
    answer = run_chat(
        get_llm(),
        question,
        nodes,
        read_page=_read_page(ctx.client),
        language=language,
        today=_today_text(language),
        schedule=_schedule_text(ctx.client, settings, language),
    )

    ctx.client.table("chat_messages").insert(
        {
            "user_id": ctx.user_id,
            "question": question,
            "answer": answer.answer,
            "sources": answer.sources,
        }
    ).execute()

    return answer.model_dump()
