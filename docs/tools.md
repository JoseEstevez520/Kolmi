# Actions as tools

How Kolmi's actions become tools for a model: the chat's, and anyone's own AI over the MCP. The
MCP server itself, its tokens and what each role gets over it are in [mcp.md](mcp.md).

## One way in: `invoke`

Every feature is an action in the registry (`backend/app/actions/registry.py`). Whoever runs
one, the web's route, the chat or the MCP, goes through `invoke(action, ctx, args)`:

1. The caller's status (`_check_status`). Empty for now: `approved` is still checked by the
   handlers that need it (notes, files, the export). The `active | pending | blocked` status of
   "Users from the admin panel" goes here, once.
2. The caller's role against the action's `min_role`. A student calling an admin action
   directly gets a 403, whatever the surface.
3. The params, validated with Pydantic. Bad params are a 422 whose message names the field.
4. The handler. Checks that depend on the data (whose note, whose file) stay in it.

## Where an action is offered

Each `Action` says three things, all `False` unless set, so a new action is never offered by
accident:

| Field | Means |
|---|---|
| `read_only` | It changes nothing. A model may run it freely; anything else is confirmed first. |
| `tool` | It is offered to a model at all. |
| `mcp` | It is offered over the MCP too. Implies `tool`. |

`tools.offered(ctx, surface)` gives the actions a caller has on a surface (`chat` or `mcp`):
those with `tool` (and `mcp`, for the MCP) whose `min_role` the caller has.

Never tools: signing up (`register_profile`), a file's signed link (`download_file`), the chat
itself (`ask_chat`, which spends the class's model), the settings form (`update_settings`) and
the caller's own profile (`get_profile`). Never over the MCP: settings, and the timetable's
writes, whose days are indexes into the settings.

## Written for a model

A tool's description is all a model knows of it, so each one says what it does, when to use it
and when not, and every param has a `Field(description=...)`. Tools are shaped as tasks, not
copied from the routes: `move_node` takes "first", "after a sibling" or "last", where the web's
drag and drop resends a whole order with `reorder_nodes` (not a tool).

Errors say how to recover: "There is no node 12; list_nodes shows the tree", not a bare 404. A
model reads the message and tries again.

## Who may act at all

Before the role, `invoke` checks the caller's status: only an active member gets in. Someone
pending, blocked or with no profile gets a 403 that says why and what to do. An action marked
`any_status` runs for them anyway: their profile, signing up and deleting their own account,
nothing else. The routes that aren't actions (uploading a file, the export) make the same check,
so there is no way in around it.

The class's people (`list_users`, `set_role`, `set_status`, `delete_user`, `update_my_name`) are
chat tools for whoever may use them and never MCP ones; `delete_my_account` is no tool at all.

A personal token (the MCP's) reaches only the actions offered over the MCP: `invoke` refuses any
other with a token, whatever the route, so an AI can't go round the MCP's list through the API.

## Light answers

The API returns full rows. On the tool path, `tools.answer` drops what only the web draws
(`content_web`, the page's OpenUI Lang) at any depth and cuts an answer past 12,000 characters,
with a line saying how to ask for less. `view_node` with `include_web` hands the web back: a
read, open to every member as the page is in the app, so an admin's AI can change what is there
with `write_page_web` rather than write it all. Past the cap the answer says the web came cut and
is not to be edited as it is. `tools.run_tool(ctx, name, args, surface)` runs one call
and always answers text, errors included. It doesn't ask for confirmation: the chat (a proposal
the person confirms, see below) and the MCP client (from `destructiveHint`) do that before calling.

## Tools in the chat

`ask_chat` offers the model `read_page` and `search_web` plus the registry's actions on surface
`chat` for the asker's role (`tools.offered(ctx, "chat")`). Actions with `tool=False`
(`ask_chat`, `delete_my_account`, tokens, `update_settings`...) never.

- A `read_only` action runs inside the model's loop through `tools.run_tool`: light answers, the
  12,000-character cap.
- Anything else is not run. `registry.check` validates it (status, role, params: the checks of
  `invoke`, without the handler) and it is kept as a proposal: a row in `chat_proposals`
  (`message_id`, `user_id`, `tool`, `args`, `status` `pending | running | done | cancelled`,
  `result`, `decided_at`). The model is told it was proposed. Every write is a proposal,
  `create_note` included.
- `ask_chat` answers `{answer, sources, message_id, proposals: [{id, tool, args, status,
  destructive, result}]}`. `destructive` is the action's `requires_confirmation`.
- `POST /chat/confirm` (`confirm_chat_proposal`, `{proposal_id, args?}`): only the person who
  asked (anyone else gets 404), only once (claimed atomically `pending` to `running`, else 409).
  It runs through `invoke` with the confirmer's role and source `chat`; edited args are
  validated again. On an error the proposal goes back to `pending` with the error in `result`.
  If the model's loop fails and the chat answers from the index alone, nothing is proposed.
  `POST /chat/cancel` (`cancel_chat_proposal`) cancels it.
- Apply `supabase/migrations/20261010120000_chat_proposals.sql` before deploying.

Format, after looking at the references: the OpenAI Agents SDK's human-in-the-loop
(`needs_approval` gives interruptions, approve or reject by call;
[docs](https://github.com/openai/openai-agents-python/blob/main/docs/human_in_the_loop.md)),
the Vercel AI SDK's `needsApproval` and its `approval-requested` part, and LangGraph's
`interrupt()` (an editable resume value). Kolmi keeps a row per proposal on the server, not in
the client's history, keyed by its own id, with editable args like LangGraph's resume, and no
paused run: a turn ends with proposals and confirming is a new request, as AGENTS.md says. No
LangGraph.

### Streaming: `POST /chat/stream`

Same body as `ask_chat` (`{question, history?}`) and the same checks (status, chat on, daily
limit, empty question), which fail as plain HTTP errors before anything streams. The answer is
`text/event-stream` (`StreamingResponse`, no new dependency), each event `event: <name>` and
`data: <json>`:

| Event | Data |
|---|---|
| `status` | `{"text": "Reading page 20..."}`, when a tool runs |
| `token` | `{"text": "..."}`, a piece of the answer |
| `proposal` | `{id, tool, args, status, destructive, result}`, as in `ask_chat`'s `proposals` |
| `done` | `{}`, always last on success |
| `error` | `{"message": "..."}`, the stream ends here (no `done`) |

The tokens add up to an OpenUI Lang program (`root = Answer([...])`) of Text, Callout, Steps,
Table, Chart, Cards, CodeBlock, `Sources([ids])` and `Proposal(id)`, not JSON. A write is stored
as a `pending` proposal the moment the model proposes it (never run) and the tool's reply gives
the model its id for `Proposal(id)`. The message is saved at the end (or when the reader leaves),
with the ids in `Sources` as its sources. `ask_chat` is unchanged. The model side is
`stream_with_tools` in `agents/client.py`; the route is `app/chat_api.py`.

Evals: `backend/evals/chat_tools.json`, run with `.venv/bin/python -m evals.run_chat_evals` from
`backend/` (same flags as `run_mcp_evals`: `--role`, `--repeat`, `--only`, `--verbose`).

The web's proposal card is not built: elastic-ui has no proposal card yet (`ChatTool` has only
working, done and error, and no actions), so it waits on the library.

## Who did what, and from where

`ai_log` has `user_id` (null for the daily pass, which acts on its own) and `source`
(`pass | chat | mcp | web`); `notes` has `source` (`web | chat | mcp`) and an optional
`source_url` (a Moodle link, a commit). Whoever builds the `Context` says where the call comes
from (`Context.source`, `web` by default). Apply
`supabase/migrations/20261006120000_sources.sql` before deploying this: the web's notes write
`source`.

`update_node` no longer takes `content_md` or `content_web` (and refuses unknown fields): a
page's content changes only through the pass and, later, `write_page`, which keeps a version.

## Pages from outside the pass

`write_page` puts Markdown into a page without waiting for the daily pass. In `replace` mode
the Markdown becomes the page as it is, so it is for text the caller wrote. In `merge` mode the
notes agent folds it into the page and strips names and private data, so it is for material from
Moodle, a repo or a forum. It runs in the background: the action answers `queued` at once and
`view_ai_log` shows the outcome (`updated`, or `flagged` with the error), with who asked and from
where. `rebuild_page` makes the web again from the page's Markdown. Every rewrite keeps the
previous content in `node_versions`; `list_versions` lists them (a preview, never the web) and
`restore_version` (confirmed) brings one back, saving the current content first. In the app,
an admin sees the same list as a page's History (`PageHistory.vue`, in the page's top bar), and
restores from it through the same two actions.

## Searching the pages

`search_pages` (read only, over the MCP) runs the same hybrid search as the chat's passages
(`app/rag/`): full text and vectors over `page_chunks`, merged with Reciprocal Rank Fusion, one
result per page in the usual `{id, title, snippet}` shape. Without an index (no embedding key, or
nothing indexed yet) it falls back to plain word matching, so the tool never goes dark.

The index is kept by hooks, never by the caller. `app/rag/index.py` re-chunks and embeds a page at
the end of the daily pass (only the pages it wrote), after `write_page` (replace and merge),
`rebuild_page` and `restore_version`. Not `write_page_web`: the Markdown is unchanged. A page whose
Markdown hash matches its chunks is skipped, deleting a node deletes its chunks by cascade, and a
failure is logged and never fails the write. Apply
`supabase/migrations/20261010130000_page_chunks.sql` before deploying this.

## A page's web as written

`write_page_web` (admin, confirmed) sets a page's OpenUI Lang (`content_web`) exactly as given,
with no web agent in between: for a livelier page than the agent makes, written by an admin's
own AI over the MCP or in the chat. The Markdown stays as it is, the previous content is kept as
a version, and the AI log says who and from where (`source_url` in the reason). It runs at once:
no model is called.

Nothing is saved unless the page holds up, and a page is never left blank. `page_problems` in
`agents/web.py` checks it, and each problem names its line and what to change:

- `openui.problems`: it parses, the root is a `Page` with blocks, every component is in the
  catalogue, every call's arguments match its props (types, enums, required ones, a part in a
  place that takes it, no unknown keys), every reference is defined and every statement is
  reached from the root (one nothing uses would be dropped silently). It reads the props from
  `page.spec.json`, the JSON Schema generated from the frontend's catalogue, matching each
  call's arguments to them in order, so no rule is written twice.
- Each `Diagram` and `Artifact` carries its drawing (`svg`, `piece`), which goes through the same
  checks a drawn one does: the renderer draws nothing for a brief alone.

The web follows the Markdown: the page's next rebuild draws it again from there.

## Bug reports

`report_bug` (any active member, web only, never a tool or an MCP action) takes a title, a
description, the page the person was on and, sent by the app itself, a short environment line
(browser, screen width, theme, language; nothing that identifies the person, 300 characters at
most). The Settings dialog adds it on its own; the chat adds it when the person confirms the
proposal, since the model can't know the browser. It saves a row in `bug_reports` at once and judges it
in the background, like `write_page`: one model call, no loop (`app/bugs.py`), on the instance's
own key (`get_llm()`). The verdict is `{genuine, severity, kind, title, body, reason}`, where `kind` is `bug` or `enhancement` (a feature request or an idea): the title and
body are rewritten for a developer without personal data, and the reason is kept. The row's
`status` says where it ended up:

| Status | Means |
|---|---|
| `pending` | Not judged yet, or judged genuine while GitHub isn't set up: an admin sees the verdict and files it. |
| `issue` | Filed: `issue_url` has the link. |
| `discarded` | Judged not genuine (trolling, noise, not about the app); the reason stays. |
| `failed` | The model or GitHub failed; the report is kept. |

A genuine report becomes an issue through GitHub's REST API (`POST /repos/{owner}/{repo}/issues`,
plain `httpx`), labelled `bug-report`, `severity:low|medium|high` and `bug` or `enhancement`, with an `Environment:` line next to the page. The judge sees the environment as context. Set `GITHUB_TOKEN` (a
fine-grained token with only "Issues: read and write" on that repo) and `GITHUB_REPO`
(`owner/name`) in the server's `.env`; they never reach the browser. A student may send
`bug_report_daily_limit` reports a day (default 5, set in `settings`); admins have no cap.
`my_bug_reports` (read only, not a tool) lists the caller's own reports with status, reason and
issue link.

Before judging, the backend lists the repo's open issues (`GET /repos/{owner}/{repo}/issues`, pull
requests skipped, at most 30 titles) and hands them to the same judging call, which answers
`duplicate_of`: the number of an issue that is the same problem, or null. A duplicate is not
opened again: a short comment goes on the existing issue ("Another person reported this: ...",
never a name or an email) that also says how many people have reported it, counted from our own
table ("Reported by 3 people so far."), and the report is `issue` with that issue's link and
`verdict.duplicate_of`. If the list can't be fetched, the report is filed normally. The token
needs only Issues read and write.

Admins see the whole queue. `list_bug_reports` (read only, admin, not a tool) returns every report
with its author's name, status, reason and issue link. `file_bug_report(id)` and
`discard_bug_report(id, reason?)` (admin, confirmed, web only, never a tool or MCP) file a
pending, failed or discarded report now, skipping the genuine check, through the same filing path
(a discarded or failed one with no write-up is judged once more for a clean title and body), or
discard it; a filed report can't be filed again or discarded. The UI is `/admin/reports`.

Apply `supabase/migrations/20261013120000_bug_reports.sql` and `supabase/migrations/20261013140000_bug_report_environment.sql` before deploying.

## Decisions taken

- `approved` stays in the handlers until the user status replaces it.
- The tree's and the timetable's writes are chat tools and, for an admin, MCP ones too: an admin's own AI can lay out the class from outside. Users and settings stay in the app and the chat.
- `update_settings` is not a tool for now.
- `update_settings`'s own admin check went: `invoke` covers it.
- Tool answers are capped at 12,000 characters.
- In the chat every write is a proposal, stored server-side and confirmed in a new request; no
  LangGraph.
