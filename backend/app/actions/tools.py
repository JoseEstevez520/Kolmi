from __future__ import annotations

import json
from typing import Any, Literal

from fastapi import HTTPException
from pydantic import BaseModel

from ..auth import Context
from .registry import Action, get_registry, has_role, invoke

# Where a tool is offered: the in-app chat, or an outside client through the MCP.
Surface = Literal["chat", "mcp"]


def offered(ctx: Context, surface: Surface) -> list[Action]:
    """The actions this caller is offered as tools on a surface: it never lists what it
    would refuse."""
    return [
        a
        for a in get_registry().values()
        if a.tool and (surface == "chat" or a.mcp) and has_role(ctx, a.min_role)
    ]


def schemas(ctx: Context, surface: Surface) -> list[dict[str, Any]]:
    return [a.tool_schema() for a in offered(ctx, surface)]


# A tool's answer goes back into a model's context, so it is kept short.
TOOL_ANSWER_CHARS = 12_000
# Fields a model never needs: the page as the web draws it is large and unreadable to it.
HEAVY_KEYS = frozenset({"content_web"})


def light(value: Any) -> Any:
    """The value without what a model can't use."""
    if isinstance(value, BaseModel):
        return light(value.model_dump())
    if isinstance(value, dict):
        return {k: light(v) for k, v in value.items() if k not in HEAVY_KEYS}
    if isinstance(value, list):
        return [light(v) for v in value]
    return value


def answer(value: Any) -> str:
    text = json.dumps(light(value), ensure_ascii=False, default=str)
    if len(text) <= TOOL_ANSWER_CHARS:
        return text
    more = len(text) - TOOL_ANSWER_CHARS
    return (
        text[:TOOL_ANSWER_CHARS]
        + f"\n[Cut: {more} more characters. Ask for less: one node with view_node, a status or a limit.]"
    )


def run_tool(ctx: Context, name: str, args: dict[str, Any] | None, surface: Surface) -> str:
    """Run a tool the model asked for and say what came out, as text for the model.

    It doesn't ask for confirmation: the chat and the MCP do that before calling.
    """
    found = next((a for a in offered(ctx, surface) if a.name == name), None)
    if found is None:
        return f"There is no tool {name}. The tools you have are the ones listed."
    try:
        return answer(invoke(found, ctx, args))
    except HTTPException as exc:
        return f"Error {exc.status_code}: {exc.detail}"
