from __future__ import annotations

from typing import Any, Literal

from ..auth import Context
from .registry import Action, get_registry, has_role

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
