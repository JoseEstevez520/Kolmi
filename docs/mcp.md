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

## Pages as resources

Each shared page is a resource, `kolmi://page/{id}` (the id `list_nodes` gives), with a template for
it: a client can read a page without calling a tool. It reads as the export writes it
(`export.page_markdown`): the title, where it sits, its Markdown, with a link to another page going
to that page's own resource. Only pages with content; never a raw note, a file or the web. Any
active member reads them; anything else is the spec's "resource not found" (-32002).

## The prompt

`material_to_notes` ("Turn this material into class notes"), with an optional `material` (pasted,
or where it is), walks an AI through what Kolmi expects: read the tree first, check what the pages
already say (`search_pages`, `view_node`), one note per topic in its own words with its
`source_url` and a page hint, nothing personal or secret, and a word at the end on what it did. An
admin's version folds the material into the page with `write_page` in `merge` mode instead of
leaving notes. The text is in `app/mcp_server.py`.

## Connect your AI

Settings → Connect your AI makes a token with a name and shows it once, with the instructions for
each kind of client already holding the instance's address and the token. After that only its
prefix is listed, with when it was last used, and it can be revoked. The clients and their
formats live in `frontend/src/lib/mcp-clients.js`, each with the official page it was taken from:

| Client | How | Source |
|---|---|---|
| Claude Code | `claude mcp add --transport http kolmi <url> --header "Authorization: Bearer <token>"` | https://code.claude.com/docs/en/mcp |
| Gemini CLI | `gemini mcp add --transport http --header "Authorization: Bearer <token>" kolmi <url>` | google-gemini/gemini-cli, `docs/tools/mcp-server.md` |
| Codex CLI | the token from an environment variable: `codex mcp add kolmi --url <url> --bearer-token-env-var KOLMI_TOKEN` | openai/codex, `codex-rs/cli/src/mcp_cmd.rs` |
| Any other | the address, the `Authorization` header, and an `mcpServers` JSON in Claude Code's `.mcp.json` shape | https://code.claude.com/docs/en/mcp |

Codex keeps the token in an environment variable rather than its config; an `export` typed in a
shell stays in its history, so it is better set where the shell's own secrets go.

Editors with an install link (Cursor, VS Code) and their own JSON (Windsurf) aren't listed yet:
their official pages couldn't be read when this was written, and their formats change, so they wait
until checked. Chat apps (Claude, ChatGPT) want the OAuth sign-in, still to come.

## Evals

`backend/evals/mcp_tools.json` holds requests a member might make of their AI, each with the tool
(and arguments) its first call should go to, and what it must not call. `run_mcp_evals` gives a
model the tools exactly as `/mcp` lists them for the role, the server's instructions and the
class's tree, and judges the first call; it calls no Kolmi tool and touches no database. From
`backend/`, with `LLM_*` set as for the pass (or `--model`, `--base-url`, `--api-key-env` for another):

```bash
.venv/bin/python -m evals.run_mcp_evals
.venv/bin/python -m evals.run_mcp_evals --role student --repeat 3
.venv/bin/python -m evals.run_mcp_evals --only admin-merge --verbose
```

A failing case points at a description to rewrite, not at the model. `tests/test_evals.py` keeps
the cases in step with the tools each role is offered.

## The daily cap

Each note costs a gatekeeper call, so a student's AI leaves at most `mcp_daily_notes` notes a day
(a class setting, 30 by default), counted from midnight, Madrid time. Past it, `create_note` answers
a 429 that says when they can write again, and that the app has no cap. Admins have none; notes
from the app don't count.

## Not yet

Text only: files over the MCP come later. The OAuth sign-in for chat apps, and the editors' install
links once their formats are checked.
