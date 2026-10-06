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

from mcp.shared.exceptions import MCPError

from . import tokens
from .actions.registry import Action
from .actions.tools import offered, run_tool
from .auth import Context, _profile, check_active, status_of, token_context
from .export import page_markdown, shared_pages
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


async def _list_resources(_ctx: Any, _params: types.PaginatedRequestParams | None) -> types.ListResourcesResult:
    def pages() -> list[types.Resource]:
        return [
            types.Resource(
                name=page["title"],
                uri=page_uri(page["id"]),
                description=" > ".join(trail) or None,
                mime_type="text/markdown",
            )
            for page, trail in shared_pages(_shared_nodes(_caller()))
        ]

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
