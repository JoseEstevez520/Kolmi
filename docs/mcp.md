# The MCP

Kolmi is an MCP server for each member's own AI: the assistant someone already uses (a coding
agent, an editor, a chat app) reads the class's pages and leaves notes in Kolmi as that person. The
case it is for: someone's AI reads their Moodle or a GitHub repo and writes it up as class notes.
Reading is free; what changes something the client confirms first, from the tool's own hints.

It is the same instance and the same FastAPI app as the rest, at `/mcp`. There is no other service.

## How it is built

The official Python SDK (`mcp`, 2.x): its low-level `Server`, with the tools listed and called by
two handlers, on its streamable HTTP transport (`StreamableHTTPSessionManager`), stateless and
answering JSON. Stateless means no session store, so it runs in the API's one worker as any route
does. `app/mcp_server.py` holds it; `app/main.py` adds the `/mcp` route and runs the transport in
the app's lifespan.

The SDK's high-level `MCPServer` infers each tool from a Python function's signature. Kolmi's tools
are its registry's actions, and which ones a caller gets depends on their role, so the low-level
server lists them per caller (`tools.offered(ctx, "mcp")`) with each action's own JSON Schema and
description, and runs them with `tools.run_tool`, through `invoke`.

| Action | Tool |
|---|---|
| `read_only` | `readOnlyHint` |
| `requires_confirmation` | `destructiveHint`: the client asks before calling |
| the params' model | `inputSchema` |
| the description, written for a model | `description` |

## Tokens

A personal token is `kolmi_` and 32 random bytes from `secrets` (256 bits). It is shown once, when
it is made, and only its SHA-256 hash is kept in `api_tokens`, with a prefix to tell tokens apart in
a list. A token this long can't be guessed, so a slow password hash buys nothing; a plain hash lets
each request be checked with one lookup. Each use sets `last_used_at`. A token never goes into a
log, an error or a tool's answer.

- **Made, listed and revoked from the web** (`create_my_token`, `list_my_tokens`,
  `revoke_my_token`): never tools, so an AI can't make or see a token.
- **Acts as its owner**, with their role and status. A token whose owner is pending or blocked gets
  a 401 at `/mcp`.
- **Revoked when its owner loses access:** `on_access_lost`, called when someone is blocked, made a
  student or deleted, revokes all their tokens.
- **Only the MCP's tools:** with a token, `invoke` refuses every action not offered over the MCP,
  whatever the route, and so do the upload and export routes. Managing people, settings, tokens or
  one's account is done in the app.

The bearer token goes in the `Authorization` header, as the MCP spec has it. It is checked with the
SDK's own middleware (`BearerAuthBackend`, `RequireAuthMiddleware`) and Kolmi's verifier. A request
without a good one gets a 401 with `WWW-Authenticate: Bearer`.

### Why personal tokens, not OAuth yet

The MCP authorization spec makes an HTTP server an OAuth 2.1 resource server: the client finds
the authorization server from the server's protected-resource metadata (RFC 9728), signs the
person in there, and gets a token issued for this server. Kolmi has no authorization server yet,
so it serves no metadata (pointing at one that isn't there would mislead a client), and it issues
its own tokens instead. Each is minted by this instance and good only here, which is what the
spec's audience rule is for. The coding agents and editors take a bearer token in their config;
the chat apps' connectors expect the OAuth sign-in, which is the ROADMAP's "Sign in over OAuth for
chat apps".

## What each role is offered

| | Tools |
|---|---|
| Everyone | `list_nodes`, `view_node` (with `include_web`, a page's web), `search_pages`, `list_schedule_events`, `create_note`, `update_note`, `my_notes`, `delete_note` |
| Admins, too | `write_page`, `write_page_web`, `rebuild_page`, `list_versions`, `restore_version`, `list_notes`, `view_ai_log`, `list_passes`, `run_pass` |
| Never | the class's people, the settings, the tokens, the account, `ask_chat` (the client brings its own model), the tree's own actions (`create_node`, `update_node`, `move_node`, `delete_node`: an admin's AI writes pages, not the tree), the timetable's writes, files |

A note left through the MCP has `source = 'mcp'` and, when the AI gives one, the `source_url` it
came from.

## The daily cap

Each note costs a gatekeeper call, so a student's AI leaves at most `mcp_daily_notes` notes a day
(a class setting, 30 by default), counted from midnight, Madrid time. Past it, `create_note` answers
a 429 that says when they can write again, and that the app has no cap. Admins have none; notes
from the app don't count.

## Not yet

Text only: files over the MCP come later. Pages as resources, the "turn this material into class
notes" prompt, "Connect your AI" in Settings and evals with a real client are the next batch.
