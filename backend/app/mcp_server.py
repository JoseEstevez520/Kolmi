"""Kolmi as an MCP server, at /mcp in the same app: anyone's own AI acts as them, with a personal
token (`kolmi_...`, see app/tokens.py).

Built on the official SDK's low-level server and its streamable HTTP transport, stateless and
answering JSON, so it needs no session store and runs in the API's one worker. Its tools are the
registry's (`tools.offered(ctx, "mcp")`), listed per caller and run through `invoke`, so the role,
the status and the params are checked as they are for the web. A tool that only reads says so
(`readOnlyHint`); one the app confirms first says it is destructive, so the client asks first.

The bearer token is checked with the SDK's own middleware (`BearerAuthBackend`,
`RequireAuthMiddleware`) and a verifier of Kolmi's: an unknown or revoked token, or one whose
owner isn't active, gets a 401. Kolmi issues its tokens itself and has no OAuth authorization
server yet ("Sign in over OAuth" in the ROADMAP), so no protected-resource metadata is served.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

import anyio
from mcp import types
from mcp.server.auth.middleware.auth_context import AuthContextMiddleware, get_access_token
from mcp.server.auth.middleware.bearer_auth import BearerAuthBackend, RequireAuthMiddleware
from mcp.server.auth.provider import AccessToken
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPASGIApp, StreamableHTTPSessionManager
from mcp.server.transport_security import TransportSecuritySettings
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.routing import Route

from . import tokens
from .actions.registry import Action
from .actions.tools import offered, run_tool
from .auth import Context, _profile, status_of, token_context
from .supabase_client import get_client

PATH = "/mcp"
INSTRUCTIONS = (
    "Kolmi is a class's shared notebook: notes left by its members become organized pages each "
    "night. Read the tree (list_nodes), a page (view_node) or search the pages (search_pages) "
    "before writing. Leave what someone learned as notes (create_note), one per topic, with the "
    "source_url it came from; they are private until the daily pass writes them into the pages."
)


class KolmiTokens:
    """The SDK's TokenVerifier for Kolmi's personal tokens. Never logs a token."""

    async def verify_token(self, token: str) -> AccessToken | None:
        if not tokens.is_token(token):
            return None
        ctx = await anyio.to_thread.run_sync(token_context, get_client(), token)
        # Someone pending or blocked doesn't get in through their AI either.
        if ctx is None or status_of(ctx.profile) != "active":
            return None
        return AccessToken(token=token, client_id=f"kolmi:{ctx.user_id}", subject=ctx.user_id, scopes=[])


def _caller() -> Context:
    """The context of whoever the verified token belongs to, read again for this request."""
    access = get_access_token()
    if access is None or not access.subject:  # the middleware lets nobody else through
        raise PermissionError("no verified token")
    client = get_client()
    return Context(
        user_id=access.subject, email=None, profile=_profile(client, access.subject), client=client, source="mcp"
    )


def _tool(action: Action) -> types.Tool:
    schema = action.params.model_json_schema() if action.params else {"type": "object", "properties": {}}
    return types.Tool(
        name=action.name,
        description=action.description,
        input_schema=schema,
        annotations=types.ToolAnnotations(
            read_only_hint=action.read_only,
            destructive_hint=action.requires_confirmation,
            open_world_hint=False,
        ),
    )


async def _list_tools(_ctx: Any, _params: types.PaginatedRequestParams | None) -> types.ListToolsResult:
    caller = await anyio.to_thread.run_sync(_caller)
    return types.ListToolsResult(tools=[_tool(action) for action in offered(caller, "mcp")])


async def _call_tool(_ctx: Any, params: types.CallToolRequestParams) -> types.CallToolResult:
    def run() -> str:
        return run_tool(_caller(), params.name, dict(params.arguments or {}), "mcp")

    text = await anyio.to_thread.run_sync(run)
    failed = text.startswith(("Error ", "There is no tool"))
    return types.CallToolResult(content=[types.TextContent(type="text", text=text)], is_error=failed)


server = Server("kolmi", version="1", instructions=INSTRUCTIONS, on_list_tools=_list_tools, on_call_tool=_call_tool)

# A remote server behind a bearer token: DNS rebinding protection is for local servers a browser
# could be tricked into reaching without one.
sessions = StreamableHTTPSessionManager(
    app=server,
    json_response=True,
    stateless=True,
    security_settings=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)


def route() -> Route:
    """The /mcp route, for the FastAPI app: the transport, behind the SDK's bearer checks."""
    guarded = RequireAuthMiddleware(StreamableHTTPASGIApp(sessions), required_scopes=[])
    app = AuthenticationMiddleware(AuthContextMiddleware(guarded), backend=BearerAuthBackend(KolmiTokens()))
    return Route(PATH, endpoint=app)


@asynccontextmanager
async def running():
    """The transport's task group, for the app's lifespan."""
    async with sessions.run():
        yield
