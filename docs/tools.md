# Actions as tools

How Kolmi's actions become tools for a model: the chat's, and anyone's own AI over the MCP. This
is the base the ROADMAP's "Next" builds on; the chat and the MCP themselves come later.

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

## Light answers

The API returns full rows. On the tool path, `tools.answer` drops what only the web draws
(`content_web`, the page's OpenUI Lang) at any depth and cuts an answer past 12,000 characters,
with a line saying how to ask for less. `tools.run_tool(ctx, name, args, surface)` runs one call
and always answers text, errors included. It doesn't ask for confirmation: the chat (a card with
Confirm) and the MCP client (from `destructiveHint`) do that before calling.

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
`restore_version` (confirmed) brings one back, saving the current content first.

## Decisions taken

- `approved` stays in the handlers until the user status replaces it.
- The timetable's writes are chat tools but not MCP ones.
- `update_settings` is not a tool for now.
- `update_settings`'s own admin check went: `invoke` covers it.
- Tool answers are capped at 12,000 characters.
