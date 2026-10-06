from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

from fastapi import HTTPException
from pydantic import BaseModel, ValidationError

from ..auth import Context, check_active

Handler = Callable[[Context, Optional[BaseModel]], Any]


@dataclass(frozen=True)
class Action:
    """A single feature, defined once.

    From the registry of actions we generate the API routes the web uses and,
    later, the tools the chat uses. The role and the caller's status are checked
    once, in `invoke`; checks that depend on the data (whose note, whose file)
    stay in the handler.
    """

    name: str
    description: str
    handler: Handler
    params: Optional[type[BaseModel]] = None
    method: str = "POST"
    path: Optional[str] = None
    requires_confirmation: bool = False
    min_role: str = "student"
    # Runs for a caller who isn't active: only what a pending or blocked person still needs (their
    # profile, signing up, deleting their own account).
    any_status: bool = False
    # Whether it only reads, and where it is offered as a tool: to the chat, and to the MCP.
    read_only: bool = False
    tool: bool = False
    mcp: bool = False

    @property
    def http_path(self) -> str:
        return self.path or f"/{self.name}"

    def tool_schema(self) -> dict[str, Any]:
        """OpenAI/DeepSeek function-calling schema for the future chat."""
        parameters = (
            self.params.model_json_schema()
            if self.params
            else {"type": "object", "properties": {}}
        )
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": parameters,
            },
        }


_REGISTRY: dict[str, Action] = {}


def action(
    *,
    name: str,
    description: str,
    params: Optional[type[BaseModel]] = None,
    method: str = "POST",
    path: Optional[str] = None,
    requires_confirmation: bool = False,
    min_role: str = "student",
    read_only: bool = False,
    tool: bool = False,
    mcp: bool = False,
    any_status: bool = False,
):
    def decorator(fn: Handler) -> Handler:
        _REGISTRY[name] = Action(
            name=name,
            description=description,
            handler=fn,
            params=params,
            method=method,
            path=path,
            requires_confirmation=requires_confirmation,
            min_role=min_role,
            read_only=read_only,
            tool=tool,
            mcp=mcp,
            any_status=any_status,
        )
        return fn

    return decorator


def get_registry() -> dict[str, Action]:
    return _REGISTRY


ROLES = {"student": 0, "admin": 1}


def has_role(ctx: Context, min_role: str) -> bool:
    role = (ctx.profile or {}).get("role") or "student"
    return ROLES.get(role, 0) >= ROLES[min_role]


def _check_status(ctx: Context, action: Action) -> None:
    """Whether the caller may act at all: the one place for it. Only an active member may, but
    for the few actions a pending or blocked one still needs."""
    if not action.any_status:
        check_active(ctx)


def _invalid(exc: ValidationError) -> str:
    parts = [
        f"{'.'.join(str(p) for p in e['loc']) or 'params'}: {e['msg']}" for e in exc.errors()
    ]
    return "Invalid params. " + "; ".join(parts)


def invoke(action: Action, ctx: Context, args: dict[str, Any] | None = None) -> Any:
    """Run an action for a caller: the web, the chat and the MCP all come through here."""
    _check_status(ctx, action)
    if not has_role(ctx, action.min_role):
        raise HTTPException(403, "Admin only")
    params = None
    if action.params is not None:
        try:
            params = action.params.model_validate(args or {})
        except ValidationError as exc:
            raise HTTPException(422, _invalid(exc)) from exc
    return action.handler(ctx, params)


def get_action(name: str) -> Action | None:
    return _REGISTRY.get(name)
