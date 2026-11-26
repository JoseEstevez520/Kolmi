"""Kolmi as an MCP server, at /mcp in the same app: anyone's own AI acts as them, with a personal
token (`kolmi_...`, see app/tokens.py).

Built on the official SDK's low-level server and its streamable HTTP transport, stateless and
answering JSON, so it needs no session store and runs in the API's one worker. Its tools are the
registry's (`tools.offered(ctx, "mcp")`), listed per caller and run through `invoke`, so the role,
the status and the params are checked as they are for the web. A tool that only reads says so
(`readOnlyHint`); one the app confirms first says it is destructive, so the client asks first.
The shared pages are resources too (`kolmi://page/{id}`, the export's Markdown), and one prompt
guides an AI through turning material into class notes.

The bearer token is checked with the SDK's own middleware (`BearerAuthBackend`,
`RequireAuthMiddleware`) and a verifier of Kolmi's: an unknown or revoked token, or one whose
owner isn't active, gets a 401. When `MCP_OAUTH_ENABLED` is true, `/mcp` also accepts Supabase
OAuth 2.1 access tokens and serves RFC 9728 protected-resource metadata for chat connectors.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any
from urllib.parse import urlparse

import anyio
from mcp import types
from mcp.server.auth.middleware.auth_context import AuthContextMiddleware, get_access_token
from mcp.server.auth.middleware.bearer_auth import BearerAuthBackend, RequireAuthMiddleware
from mcp.server.auth.provider import AccessToken
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPASGIApp, StreamableHTTPSessionManager
from mcp.server.transport_security import TransportSecuritySettings
from mcp.shared.auth import ProtectedResourceMetadata
from mcp.shared.exceptions import MCPError
from pydantic import AnyHttpUrl
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from starlette.types import Receive, Scope, Send

from . import tokens
from .agents.catalogue import TITLE as CATALOGUE_TITLE, URI as CATALOGUE_URI, catalogue_guide
from .actions.registry import Action
from .actions.tools import offered, run_tool
from .auth import Context, _profile, check_active, status_of, token_context, verify_jwt
from .class_settings import class_language
from .config import get_settings
from .export import page_markdown, shared_pages
from .supabase_client import get_client

PATH = "/mcp"
RESOURCE_METADATA_PATHS = (
    "/.well-known/oauth-protected-resource",
    f"/.well-known/oauth-protected-resource{PATH}",
    f"/.well-known/oauth-protected-resource/api{PATH}",
)
INSTRUCTIONS = (
    "Kolmi is a class's shared notebook: notes left by its members become organized pages each "
    "night. Read the tree (list_nodes), a page (view_node) or search the pages (search_pages) "
    "before writing. Leave what someone learned as notes (create_note), one per topic, with the "
    "source_url it came from; they are private until the daily pass writes them into the pages. "
    "Admins: before write_page_web, read the resource kolmi://catalogue: the page's components, "
    "their parameters and allowed values, examples, and how to write a figure or an interactive piece."
)


def _request_origin(scope: Scope) -> str:
    headers = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope.get("headers", [])}
    proto = (headers.get("x-forwarded-proto") or scope.get("scheme") or "http").split(",")[0].strip()
    host = (headers.get("x-forwarded-host") or headers.get("host") or "").split(",")[0].strip()
    if not host:
        host_name, port = scope.get("server") or ("localhost", 8000)
        default_port = (proto == "http" and port == 80) or (proto == "https" and port == 443)
        host = host_name if default_port or port is None else f"{host_name}:{port}"
    return f"{proto}://{host}"


def _origin(scope: Scope) -> str:
    configured = get_settings().public_url.strip().rstrip("/")
    if configured:
        parsed = urlparse(configured)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
        return configured
    return _request_origin(scope)


def _public_mcp_url(scope: Scope) -> str:
    configured = get_settings().public_url.strip().rstrip("/")
    if configured:
        return configured if configured.endswith(PATH) else f"{configured}{PATH}"
    return f"{_request_origin(scope)}{PATH}"


def _verify_personal_token(token: str) -> AccessToken | None:
    ctx = token_context(get_client(), token)
    # Someone pending or blocked doesn't get in through their AI either.
    if ctx is None or status_of(ctx.profile) != "active":
        return None
    return AccessToken(token=token, client_id=f"kolmi:{ctx.user_id}", subject=ctx.user_id, scopes=["mcp"])


def _verify_oauth_token(token: str) -> AccessToken | None:
    client = get_client()
    claims = verify_jwt(client, token)
    if not claims:
        return None
    user_id = str(claims["sub"])
    profile = _profile(client, user_id)
    if status_of(profile) != "active":
        return None
    settings = get_settings()
    resource = settings.public_url.strip().rstrip("/")
    if resource and not resource.endswith(PATH):
        resource += PATH
    audience = claims.get("aud")
    audiences = audience if isinstance(audience, list) else [audience]
    client_id = claims.get("client_id")
    exp = claims.get("exp")
    if (not resource or resource not in audiences
            or claims.get("iss") != f"{settings.supabase_url.rstrip('/')}/auth/v1"
            or not isinstance(client_id, str) or not client_id
            or not isinstance(exp, (int, float))):
        return None
    raw_scope = claims.get("scope")
    scopes = raw_scope.split() if isinstance(raw_scope, str) else []
    expires_at = int(exp)
    return AccessToken(
        token=token,
        client_id=client_id,
        subject=user_id,
        scopes=scopes,
        expires_at=expires_at,
    )


class KolmiTokens:
    """The SDK's TokenVerifier for Kolmi's personal tokens and, when enabled, Supabase OAuth JWTs.
    Never logs a token."""

    async def verify_token(self, token: str) -> AccessToken | None:
        if tokens.is_token(token):
            return await anyio.to_thread.run_sync(_verify_personal_token, token)
        if not get_settings().mcp_oauth_enabled:
            return None
        return await anyio.to_thread.run_sync(_verify_oauth_token, token)


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


# -- the pages as resources: kolmi://page/{id} -------------------------------------------------------

PAGE_URI = "kolmi://page/{id}"
# The spec's "resource not found".
NOT_FOUND = -32002
EXPORT_COLUMNS = "id, parent_id, kind, title, position, content_md"


def page_uri(node_id: int) -> str:
    return PAGE_URI.format(id=node_id)


def _shared_nodes(caller: Context) -> list[dict[str, Any]]:
    """The tree with each page's Markdown, as the export reads it: only the shared pages, never a
    raw note or a file. Reading is open to any active member."""
    check_active(caller)
    return caller.client.table("nodes").select(EXPORT_COLUMNS).execute().data


def _is_admin(caller: Context) -> bool:
    return (caller.profile or {}).get("role") == "admin"


async def _list_resources(_ctx: Any, _params: types.PaginatedRequestParams | None) -> types.ListResourcesResult:
    def pages() -> list[types.Resource]:
        caller = _caller()
        found = [
            types.Resource(
                name=page["title"],
                uri=page_uri(page["id"]),
                description=" > ".join(trail) or None,
                mime_type="text/markdown",
            )
            for page, trail in shared_pages(_shared_nodes(caller))
        ]
        if _is_admin(caller):  # it is for write_page_web, which only admins have
            found.append(
                types.Resource(
                    name=CATALOGUE_TITLE,
                    uri=CATALOGUE_URI,
                    description="The components a page's web is built from, with their parameters, allowed values, when to use each, examples, and how to write a figure or an interactive piece. Read it before write_page_web.",
                    mime_type="text/markdown",
                )
            )
        return found

    return types.ListResourcesResult(resources=await anyio.to_thread.run_sync(pages))


async def _list_resource_templates(
    _ctx: Any, _params: types.PaginatedRequestParams | None
) -> types.ListResourceTemplatesResult:
    return types.ListResourceTemplatesResult(
        resource_templates=[
            types.ResourceTemplate(
                name="page",
                uri_template=PAGE_URI,
                description="One of the class's shared pages, as Markdown. Its id is the one list_nodes gives.",
                mime_type="text/markdown",
            )
        ]
    )


async def _read_resource(_ctx: Any, params: types.ReadResourceRequestParams) -> types.ReadResourceResult:
    uri = str(params.uri)
    if uri == CATALOGUE_URI:

        def guide() -> str | None:
            caller = _caller()
            check_active(caller)
            return catalogue_guide(class_language(caller.client)) if _is_admin(caller) else None

        text = await anyio.to_thread.run_sync(guide)
        if text is None:
            raise MCPError(NOT_FOUND, f"Kolmi has no resource {uri}: pages are {PAGE_URI}")
        return types.ReadResourceResult(contents=[types.TextResourceContents(uri=uri, mime_type="text/markdown", text=text)])
    prefix = PAGE_URI.split("{")[0]
    node_id = uri[len(prefix) :] if uri.startswith(prefix) else ""
    if not node_id.isdigit():
        raise MCPError(NOT_FOUND, f"Kolmi has no resource {uri}: pages are {PAGE_URI}")

    def read() -> str | None:
        return page_markdown(_shared_nodes(_caller()), int(node_id), page_uri)

    text = await anyio.to_thread.run_sync(read)
    if text is None:
        raise MCPError(NOT_FOUND, f"There is no shared page {node_id}; list_nodes shows the tree")
    return types.ReadResourceResult(contents=[types.TextResourceContents(uri=uri, mime_type="text/markdown", text=text)])


# -- the prompt: turn this material into class notes -------------------------------------------------

PROMPT = "material_to_notes"
PROMPT_TITLE = "Turn this material into class notes"

_STEPS_COMMON = """How Kolmi works: the class shares one notebook. Notes stay private until the nightly pass reads
them, strips names and private data, and writes them into the class's pages. A note is a
contribution to a page, not a page of its own.

1. Read the tree first, with list_nodes: the class's sections and pages, and what each one covers.
2. For each topic in the material, check what the class already has: search_pages for its words,
   then view_node on the page it would go in. Leave out what the page already says well; bring
   what is new, and say so when something there is wrong.
"""

_STEPS_STUDENT = """3. Split the material by topic and leave one note per topic, with create_note:
   - content: Markdown, in your own words, that someone reading only this note can follow. Code
     in code blocks, short lists where they help, no filler.
   - node_id: the page it belongs to, from list_nodes, as a hint. Leave it out when nothing fits;
     the pass will find the place.
   - source_url: where it came from (the Moodle page, the repo file or commit, the document).
   If create_note says you've reached today's limit, stop there and tell me.
"""

_STEPS_ADMIN = """3. You're an admin of this class: rather than leave notes, fold the material straight into the
   page it belongs to, with write_page in mode "merge" and one call per page:
   - node_id: the page, from list_nodes;
   - markdown: the material for that page, by topic, in your own words;
   - source_url: where it came from.
   The notes agent folds it into what the page already has and strips names and private data;
   view_ai_log shows when it is done. Keep "replace" for a page you've written whole yourself.
   When a topic needs a page that isn't there, tell me: pages are made in the app.
"""

_STEPS_END = """4. Leave out anything personal about anyone (names, emails, grades, who said what) and anything
   secret (passwords, tokens, keys).
5. Explain and summarise rather than copy: quote only the short bits that matter, such as a
   definition or a command.
6. When you're done, tell me what you wrote and where, and what you left out and why.
"""


def material_prompt(material: str | None, admin: bool) -> str:
    what = material.strip() if material and material.strip() else "what I share or point you to in this conversation"
    steps = _STEPS_COMMON + (_STEPS_ADMIN if admin else _STEPS_STUDENT) + _STEPS_END
    return f"Turn this material into notes for my class's shared notebook in Kolmi.\n\nMaterial: {what}\n\n{steps}"


async def _list_prompts(_ctx: Any, _params: types.PaginatedRequestParams | None) -> types.ListPromptsResult:
    return types.ListPromptsResult(
        prompts=[
            types.Prompt(
                name=PROMPT,
                title=PROMPT_TITLE,
                description="Read a source (a Moodle page, a repo, a document) and write it into the class's notebook the way Kolmi expects: the tree first, one note per topic, each with where it came from.",
                arguments=[
                    types.PromptArgument(
                        name="material",
                        description="What to turn into notes: paste it, or say where it is (a link, a repo, a file).",
                        required=False,
                    )
                ],
            )
        ]
    )


async def _get_prompt(_ctx: Any, params: types.GetPromptRequestParams) -> types.GetPromptResult:
    if params.name != PROMPT:
        raise MCPError(-32602, f"Kolmi has no prompt {params.name}; it has {PROMPT}")
    caller = await anyio.to_thread.run_sync(_caller)
    admin = (caller.profile or {}).get("role") == "admin"
    text = material_prompt((params.arguments or {}).get("material"), admin)
    return types.GetPromptResult(
        description=PROMPT_TITLE,
        messages=[types.PromptMessage(role="user", content=types.TextContent(type="text", text=text))],
    )


server = Server(
    "kolmi",
    version="1",
    instructions=INSTRUCTIONS,
    on_list_tools=_list_tools,
    on_call_tool=_call_tool,
    on_list_resources=_list_resources,
    on_list_resource_templates=_list_resource_templates,
    on_read_resource=_read_resource,
    on_list_prompts=_list_prompts,
    on_get_prompt=_get_prompt,
)

# A remote server behind a bearer token: DNS rebinding protection is for local servers a browser
# could be tricked into reaching without one.
sessions = StreamableHTTPSessionManager(
    app=server,
    json_response=True,
    stateless=True,
    security_settings=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)


class _GuardedMCP:
    """Wraps the MCP streamable HTTP transport with `RequireAuthMiddleware`, advertising the
    RFC 9728 `resource_metadata` URL on 401 responses when OAuth is enabled."""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        settings = get_settings()
        metadata_url = (
            AnyHttpUrl(f"{_origin(scope)}/.well-known/oauth-protected-resource{PATH}")
            if settings.mcp_oauth_enabled
            else None
        )
        required_scopes = []
        middleware = RequireAuthMiddleware(
            self.app,
            required_scopes=required_scopes,
            resource_metadata_url=metadata_url,
        )
        await middleware(scope, receive, send)


async def _protected_resource_metadata(request: Request) -> Response:
    settings = get_settings()
    if not settings.mcp_oauth_enabled:
        return JSONResponse({"detail": "Not found"}, status_code=404)
    metadata = ProtectedResourceMetadata(
        resource=_public_mcp_url(request.scope),
        authorization_servers=[f"{settings.supabase_url.rstrip('/')}/auth/v1"],
    )
    return JSONResponse(
        metadata.model_dump(mode="json", exclude_none=True),
        headers={"Cache-Control": "public, max-age=3600"},
    )


def metadata_routes() -> list[Route]:
    """RFC 9728 OAuth 2.0 Protected Resource Metadata endpoints, active when MCP_OAUTH_ENABLED is true."""
    return [
        Route(path, endpoint=_protected_resource_metadata, methods=["GET"])
        for path in RESOURCE_METADATA_PATHS
    ]


def route() -> Route:
    """The /mcp route, for the FastAPI app: the transport, behind the SDK's bearer checks."""
    guarded = _GuardedMCP(StreamableHTTPASGIApp(sessions))
    app = AuthenticationMiddleware(AuthContextMiddleware(guarded), backend=BearerAuthBackend(KolmiTokens()))
    return Route(PATH, endpoint=app)


@asynccontextmanager
async def running():
    """The transport's task group, for the app's lifespan."""
    async with sessions.run():
        yield
