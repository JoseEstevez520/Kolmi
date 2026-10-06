from __future__ import annotations

import json
from dataclasses import replace
from typing import Any, Callable, Literal

from fastapi import HTTPException
from pydantic import BaseModel

from ..auth import Context
from .registry import Action, check, get_registry, has_role, invoke

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
# How many changes the chat may propose on one answer: a flood is a model gone wrong.
MAX_PROPOSALS = 5


def light(value: Any, keep: frozenset[str] = frozenset()) -> Any:
    """The value without what a model can't use, but for the heavy fields in `keep`."""
    if isinstance(value, BaseModel):
        return light(value.model_dump(), keep)
    if isinstance(value, dict):
        return {k: light(v, keep) for k, v in value.items() if k not in HEAVY_KEYS - keep}
    if isinstance(value, list):
        return [light(v, keep) for v in value]
    return value


def answer(value: Any, keep: frozenset[str] = frozenset()) -> str:
    text = json.dumps(light(value, keep), ensure_ascii=False, default=str)
    if len(text) <= TOOL_ANSWER_CHARS:
        return text
    more = len(text) - TOOL_ANSWER_CHARS
    if keep:
        # A web cut short can't be edited: say so, rather than let it pass for the whole page.
        hint = (
            "The page's web is longer than one answer holds, so what came is not the whole of it: "
            "don't edit it as it is. Write the page anew from its Markdown with write_page_web."
        )
    else:
        hint = "Ask for less: one node with view_node, a status or a limit."
    return text[:TOOL_ANSWER_CHARS] + f"\n[Cut: {more} more characters. {hint}]"


def _asked_for_web(args: dict[str, Any] | None) -> bool:
    flag = (args or {}).get("include_web")
    return flag is True or str(flag).lower() in ("true", "1")


def run_tool(ctx: Context, name: str, args: dict[str, Any] | None, surface: Surface) -> str:
    """Run a tool the model asked for and say what came out, as text for the model.

    It doesn't ask for confirmation: the chat and the MCP do that before calling.
    """
    found = next((a for a in offered(ctx, surface) if a.name == name), None)
    if found is None:
        return f"There is no tool {name}. The tools you have are the ones listed."
    try:
        # A read asked for a page's web (view_node's include_web): it is handed back.
        keep = HEAVY_KEYS if _asked_for_web(args) else frozenset()
        return answer(invoke(found, ctx, args), keep)
    except HTTPException as exc:
        return f"Error {exc.status_code}: {exc.detail}"


def chat_tool(
    ctx: Context, proposals: list[dict[str, Any]]
) -> Callable[[str, dict[str, Any]], str]:
    """The registry's tools for the in-app chat, acting as the asker. A read runs at once; a write
    is only checked and proposed, in `proposals`, for the person to confirm, edit or cancel.
    """
    ctx = replace(ctx, source="chat")

    def run(name: str, args: dict[str, Any]) -> str:
        found = next((a for a in offered(ctx, "chat") if a.name == name), None)
        if found is None:
            return f"There is no tool {name}. The tools you have are the ones listed."
        if found.read_only:
            return run_tool(ctx, name, args, "chat")
        try:
            params = check(found, ctx, args)
        except HTTPException as exc:
            return f"Error {exc.status_code}: {exc.detail}"
        dumped = params.model_dump(mode="json", exclude_unset=True) if params is not None else {}
        proposal = {"tool": name, "args": dumped}
        if proposal not in proposals:
            if len(proposals) >= MAX_PROPOSALS:
                return (
                    f"Not proposed: there are already {MAX_PROPOSALS} proposals on this answer. "
                    "Say what is left to do and let the person ask again."
                )
            proposals.append(proposal)
        return (
            f"Proposed, not done: {name} has not run. The person sees it as a card to Confirm, "
            "Edit or Cancel. Don't call it again; say in your answer what you proposed."
        )

    return run
