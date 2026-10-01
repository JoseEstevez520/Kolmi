from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

from pydantic import BaseModel

from ..auth import Context

Handler = Callable[[Context, Optional[BaseModel]], Any]


@dataclass(frozen=True)
class Action:
    """A single feature, defined once.

    From the registry of actions we generate the API routes the web uses and,
    later, the tools the chat uses. Permissions live in the handler: it checks
    them against the caller in the context.
    """

    name: str
    description: str
    handler: Handler
    params: Optional[type[BaseModel]] = None
    method: str = "POST"
    path: Optional[str] = None
    requires_confirmation: bool = False
    min_role: str = "student"

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
        )
        return fn

    return decorator


def get_registry() -> dict[str, Action]:
    return _REGISTRY
