from typing import Any

from fastapi import Depends, FastAPI, Request

from .actions import Action, get_registry, invoke
from .auth import Context, get_context


async def _params(request: Request) -> dict[str, Any]:
    """Read action parameters: query string for GET, JSON body otherwise."""
    if request.method == "GET":
        return dict(request.query_params)
    try:
        data = await request.json()
    except Exception:
        return {}
    return data or {}


def _endpoint(action: Action):
    async def endpoint(request: Request, ctx: Context = Depends(get_context)):
        return invoke(action, ctx, await _params(request))

    endpoint.__name__ = action.name
    return endpoint


def register_routes(app: FastAPI) -> None:
    """Turn every action in the registry into an API route."""
    for action in get_registry().values():
        app.add_api_route(
            action.http_path,
            _endpoint(action),
            methods=[action.method],
            name=action.name,
            summary=action.description,
        )
