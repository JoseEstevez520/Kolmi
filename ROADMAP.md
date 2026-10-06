# Roadmap

What we're building and what's next. Open to whatever the class needs.

## Done

- [x] **Frontend** — Vue 3 + Vite + elastic-ui: login, register (class code + name), leave a
  note, my notes.
- [x] **Auth and users** — Supabase (Google + email), profile with the class code.
  Spec: [docs/authentication.md](docs/authentication.md).
- [x] **Notes** — leave a note and list "my notes".
- [x] **Content tree and admin panel** — one tree of nodes (a section groups, a page holds
  content), with a home screen and an admin panel (create, rename, edit icon and colour, move,
  reorder, delete).
- [x] **Daily pass** — a cron wakes the agent team (gatekeeper → notes → web) once a day, with
  a log (`ai_log`, `ai_passes`) and page versions.
- [x] **AI log in the admin panel** — the recent passes, what the AI did with each note or
  page, and the notes students left (`/admin/log`).
- [x] **Docker** — one image for the API and the pass; the pass runs from a host cron with
  `docker compose run --rm pass`. See [backend/README.md](backend/README.md).
- [x] **Page format (code)** — pages are OpenUI Lang (catalog plus a sandboxed artifact),
  rendered over elastic-ui with `@openuidev/vue-lang`; Markdown is derived for the RAG.
  An optional web model writes it first (any OpenAI-compatible endpoint, such as the OpenUI
  Gateway); when it fails or isn't set, DeepSeek writes the same OpenUI Lang, and Markdown is
  the last resort. The renderer loads on demand. See
  [docs/page-format.md](docs/page-format.md).
- [x] **Notes editor** — a note gets a page of its own (`/notes/new`): a title and a Tiptap
  editor that saves Markdown. Blocks come from a `/` menu or the `+` beside an empty line
  (headings, lists, checklist, quote, code, table). The draft stays in the browser, a pending
  note can be edited until the daily pass, and zen mode hides the sidebar and header.
- [x] **Spanish UI** — every screen in English and Spanish, picked by the browser's language,
  with a switch in the app. All strings go through Vue I18n.
- [x] **Settings** — language (from a list) and animations (on or off, on by default, whatever
  the system says), kept in each browser. A language switch no longer remounts the app.
- [x] **Faster pages** — the API checks the session against the project's signing keys
  instead of asking Supabase on every request, the tree is kept in the browser, and pages
  are read ahead when a link is pointed at.
- [x] **Pages in the class's language** — an admin picks the class language in the admin
  panel and the daily pass writes the shared notes and pages in it, whatever language each
  note came in. It's one row in a `settings` table; until that exists, `CLASS_LANGUAGE`
  decides (`en` by default). Apply
  [supabase/migrations/20261002120000_settings.sql](supabase/migrations/20261002120000_settings.sql)
  in the Supabase SQL editor to turn the control on.
- [x] **Navigation like the class site** — breadcrumbs whose chevrons open the siblings, the
  top-level sections in the sidebar, a table of contents, previous and next, and links between
  pages that the agents can write.
- [x] **The gatekeeper looks before it decides** — it gets the tree as an index (with each
  node's description) and reads the pages it needs with a tool. A note can carry a hint of where
  it goes, from a quiet picker in the editor; it's a hint, not an order.
- [x] **Notes first, then the page** — the notes agent writes the Markdown with a writing guide
  (apuntes-claros); the web agent makes the page from it with a page guide (apuntes-web); the main model
  draws the visuals.
- [x] **A richer page catalogue** — elastic-ui's own parts: charts, composed diagrams, tables,
  glossaries, diffs, code walkthroughs, terminal and agent replays, cards, logos, and pieces built
  from library parts in a sandboxed frame.
- [x] **Notes save themselves** — as you write, with no draft and no send button.
- [x] **The pass's schedule in the admin** — on or off, the times and the days (Madrid time),
  kept in `settings`; the host cron runs every hour with `--if-due` and the pass runs only when it
  is due. "Run now" starts it in the background, and the next run is shown.
- [x] **Attaching files stays out of the way** — a paperclip in the editor's top bar opens a small
  panel; a file dropped anywhere on the editor, or pasted, attaches too, and a note can be only
  files. Built on elastic-ui's compact `FileUpload` and `FileDropZone`.
- [x] **Where a new page goes** — the gatekeeper says where a new page sits among its siblings
  (first, after one, or last) and why; the reason shows in the AI log.
- [x] **Downloadable files** — a page can carry files to download: zips, PDFs, code. Students
  can leave them with a note too: the gatekeeper looks at each one and either attaches it to the
  page it belongs to or discards it, with its reason in the log. Up to 20 MB a file and 5 a
  note; no executables.
- [x] **Status part** — a small tinted icon in a ring, the label staying grey, for a note's, a
  pass's or an action's state, in place of the coloured badges; discarded is grey, not the danger
  colour. Built in elastic-ui (`Status`), used in Notes and the AI log.
- [x] **The class timetable** — everyone sees the week's shape, colours and all; an admin edits it
  right on the grid (elastic-ui's `Timetable`, made editable): drag an empty cell to lay a class
  down, drag a block to move it or its edge to resize it, snapped to a whole session; click to set
  its title, detail or linked page. Days are picked with `WeekPillbox`, the same part the daily
  pass's own schedule uses.
- [x] **First real pass** — tried in October 2026 with real notes, a course's files and photos of
  handwritten notes, and then cleaned up. The gatekeeper did what the plan expects in every case
  (filler, repeat, wrong hint, a note merged into a page, new pages, files attached or discarded).
  The plan and the results are in [docs/testing.md](docs/testing.md).

## Now: what real use showed

- [ ] **Better pages** — what the test showed: pages come
  out with no "To explore" section and, for some notes that would suit a drawing, no drawing
  (a flow got a diagram, three beans sharing an instance did not); the pass can't read a PDF, a zip or a photo,
  so a file only gets judged by its name. Decide whether the Gateway's web model is worth
  bringing back.
- [ ] **Gatekeeper judgement** — it isn't deterministic (the same notes were split into two pages
  in one run and merged in another) and it can fold an unrelated topic into a page (Maven inside
  Spring Boot basics). Look at it with more real notes before changing the prompt.
- [ ] **Measure a pass** — time is known (about 1.5 to 5.5 minutes for 2 to 8 notes); the cost per
  night is not. Needed to set the schedule and the model.
- [ ] **Timetable: dragging onto an occupied slot** — today a dropped block just lands where it's
  let go, even over another one. The usual calendar feel is for what's already there to shift
  aside (or refuse the drop); decide which, and build it.
- [ ] **Bug: the note's "Where does it go?" picker sometimes shows no text** — in the note editor's
  top bar (`NoteWriteView.vue`), the `NodePicker` trigger at times shows its folder icon with the
  label gone or glitched. Not reproduced yet. A likely cause: the bar's right group is `min-w-0`
  and the picker's `TruncatedText` is the only part that can shrink, so when the save status and
  the attach button's text take the room, its label truncates down to nothing. Reproduce it first
  (narrow screens, while saving, with a long path), then fix it; if the cause is in
  `PopoverMorph` or `TruncatedText`, the fix belongs in elastic-ui.

## Next: actions as tools, users and the MCP

One set of actions, used three ways: by the web, by the chat and by anyone's own AI through the
MCP. Reading is free; anything that changes something is confirmed (a button in the chat, the
client's own prompt over the MCP). The case that matters most: someone's AI reads their Moodle or
a GitHub repo and writes the class's notes in Kolmi.

- [ ] **Actions as tools** — the base for everything below.
  - One `invoke(action, ctx, args)` in the registry that validates the params, checks the caller's
    status and role, and runs the handler. The API, the chat and the MCP all go through it. Today
    the admin check lives in `api.py`'s route, so anything calling a handler directly skips it.
  - More on each `Action`: `read_only`, `tool` (offered as a tool at all: not `register_profile`,
    `download_file` or `ask_chat`) and `mcp` (offered over the MCP: never user management).
  - Tools written for a model, not copied from the routes: shaped as tasks (move a page after
    another, not resend a whole order), a description that says what it does and when to use it,
    a `Field(description=...)` on every param, light answers (no `content_web`, capped in size)
    and errors that say how to recover ("there is no page 12; `list_nodes` shows the tree").
  - Who did what, and from where: `user_id` and `source` (`pass` | `chat` | `mcp` | `web`) on
    `ai_log`; `source` and an optional `source_url` (the Moodle link, the commit) on `notes`.
  - `update_node` stops taking `content_md` and `content_web`: a page's content changes only
    through `write_page`, which keeps the version before it.
  - Tests for `invoke`: role, status, and an admin action failing when called directly.
- [ ] **Pages from outside the pass** — admin only.
  - `write_page(node_id, markdown, mode, source_url?)`. `replace`: the Markdown as it is, past the
    gatekeeper. `merge`: the notes agent folds it into what the page has, always through the
    step that strips names and private data (Moodle forums and commit authors carry them). Either
    way the version before is kept and the log says who and from where. It runs in the
    background (`build_page` and `draw_visuals` take a while): it answers "queued" and the page
    shows it is being rebuilt.
  - `rebuild_page(node_id)`: the web again from the page's Markdown.
  - `list_versions(node_id)` and `restore_version(version_id)` (confirmed), with a history and a
    restore button in the UI. Not optional once an AI can write pages.
- [ ] **Import notes that already exist** — a class that already has its notes as Markdown files
  brings them in as pages: their Markdown as it is, and the web page made from it. With
  `write_page` in `replace` mode this is mostly a loop over the files.
- [ ] **Users from the admin panel** — today there is no user management at all: the first admin
  is set by hand in Supabase and `approved` only stops notes, files and the export.
  - Two roles, `student` and `admin`, and a status apart from the role: `active` | `pending` |
    `blocked`, in place of `approved`. Blocked stops everything (reading, the chat, tokens),
    checked once in `invoke`.
  - Admin actions: `list_users` (name, email, role, status, joined, notes), `set_role` and
    `delete_user` (confirmed), `set_status`. A user's own: change their name, delete their account.
  - A class setting, "new sign-ups need approval", for when the class code leaks: a pending user
    sees a waiting screen and shows up in the admin's list.
  - The first admin from `ADMIN_EMAILS` in `.env`.
  - Never leave the class without an admin: the last one can't be demoted, blocked or deleted.
    Demoting or blocking someone revokes their tokens and clears their cached profile (it's kept
    for 30 seconds today).
  - Deleting cleanly: `files.user_id` goes from `cascade` to `set null`, so the files on shared
    pages stay; pending notes, chat sessions, tokens and Storage objects go; the account goes from
    `auth.users` too, through Supabase's admin API. Processed notes stay in the pages.
  - A "Users" tab in `/admin`. `privacy.md`: the admin sees each user's email, never their chats.
- [ ] **The MCP** — Kolmi as a server for anyone's own AI, in the same FastAPI at `/mcp`
  (streamable HTTP, the `mcp` Python SDK), so it stays one instance per class.
  - Personal tokens: `api_tokens(id, user_id, name, token_hash, prefix, last_used_at,
    created_at, revoked_at)`, shown once, revocable. `get_context` takes a Supabase session or a
    `kolmi_...` token.
  - Tools from the registry through `invoke`: `read_only` becomes `readOnlyHint`,
    `requires_confirmation` becomes `destructiveHint`. A student reads the tree, pages and
    timetable, searches, and creates, edits, lists and deletes their own notes; an admin also has
    the tree, `write_page`, `rebuild_page`, versions, received notes, the AI log and `run_pass`.
    Never users, settings or `ask_chat` (the client brings its own model).
  - Pages as resources (`kolmi://page/{id}`), from the export's Markdown.
  - A prompt, "turn this material into class notes": read the tree first, decide where each thing
    goes, one note per topic, each with its `source_url`; for an admin, `merge` into the page.
  - A daily cap on notes per student (each one costs a gatekeeper call); none for admins.
  - Text only at first; files over the MCP come later.
  - A first set of evals with a real client: do the descriptions lead it to the right tool.
  - Docs: `docs/mcp.md`, and the Moodle + GitHub + Kolmi case in both READMEs.
- [ ] **"Connect your AI" in Settings** — each person sees their own instructions, with their
  class's address and their own token already in them.
  - Make a connection with a name ("my laptop's editor"); the token shows once, and that is when
    the instructions show, with it inside.
  - A tab per kind of client, each block with a copy button: the command for command-line coding
    agents, an "add to editor" install link plus its JSON for the editors that take one, and the
    plain address and header for anything else.
  - "Or tell your agent": a text to paste into an agent that can run commands, which then adds
    the server itself.
  - Your connections: name, last used, revoke. A line saying the text is like a password: not for
    shared chats.
- [ ] **Sign in over OAuth for chat apps** — the AI chat apps' custom connectors expect OAuth, not
  a pasted token: the address, then Kolmi's own sign-in in the browser. Comes right after the MCP
  if the class mostly uses chat apps rather than coding agents; check first whether Supabase Auth
  can be the OAuth server.
- [ ] **How agents are built, in `AGENTS.md`** — today it says to move to LangGraph once there are
  loops or approval, but approval here never pauses a loop (the turn ends with a proposal; the
  confirmation is a new request). The rule to write: agents use the OpenAI SDK with their own
  loop; one agent moves to LangGraph only when it must pause and resume its own reasoning,
  survive a long run or coordinate with other agents. State that lives in the database (a thread,
  a session) is not a reason.

## Then: the chat

- [x] **Chat with the notes (RAG), pass 1: plain text** — ask the hive; it answers citing the
  page, each page's Markdown and the class timetable its source (a `read_page` tool over the
  tree's index, plus the week's schedule and today's date handed over as plain text, the same
  shape the gatekeeper gets). A second tool, `search_web` (`app/agents/search.py`, DuckDuckGo via
  `ddgs`, no account or key), is offered alongside `read_page` for whatever the class's own
  content doesn't cover — current events, something outside the class. `ChatMorph` floats over
  every screen (mounted once, beside `AppSidebar`),
  with `ChatThread` + `ChatComposer`; the admin turns it on and sets a daily limit in Settings.
  The class's own key only for now (held server-side, a row per student per day, counted and
  blocked past the limit, the same shape as `ai_log`/`ai_passes`) — a student's own browser-held
  key is still open, not built. The answer's Markdown is drawn with elastic-ui's own `Markdown`
  (not `ChatMessage`'s `text`/`ChatStream`, which only animates plain text).
- [ ] **Chat sessions** — today the model gets only the question on its own, so "and how is that
  set up?" doesn't know what "that" is, and a reload starts over.
  - `chat_sessions(id, user_id, title, summary, created_at, updated_at)`; `chat_messages` becomes
    one message a row (`session_id`, `role`, `content`, `parts jsonb`), the rows there today
    moved into an "earlier" session per user.
  - Only their owner sees them: no admin action reads them. The owner can delete them; they stay
    until then.
  - The model gets the last turns plus a summary kept on the session; `complete_with_tools` takes
    a list of messages. It also gets the page the user has open, so "explain this" works.
  - A title from a cheap call. The daily cap counts the user's messages, not tool rounds; none
    for admins.
- [ ] **Tools in the chat** — the registry's tools for the caller's role.
  - Reads run inside the model's loop, as `read_page` does.
  - Anything that changes something is proposed, not run: the backend validates the proposal and
    keeps it on the message, the web shows a card (Confirm, Edit, Cancel), and confirming calls
    `POST /chat/confirm` → `invoke`, with the result added to the session. Every write is a
    proposal at first, `create_note` included.
  - What it's for: "make a note that the exam goes up to unit 4", "save what you just explained as
    a note", "why was my note from yesterday discarded?"; for an admin, "make a Kubernetes section
    with these three pages", "move Maven out of Spring Boot", "put this text as the CI/CD
    page", "go back to yesterday's Docker page", "what did last night's pass do?", "approve the
    three pending users".
  - Evals: real requests and the tool and arguments each should lead to.
- [ ] **A chat page** — `/chat` and `/chat/:sessionId`: sessions on the left (a `Sheet` on a phone),
  the conversation wide. The bubble keeps the current session and gets "open in full"; on
  `/chat` it hides. In elastic-ui: room for actions in `ChatMorph`'s header, an action proposal
  card, a session list item and an activity line (see whether `AgentStep` will do).
- [ ] **Chat pass 2: streaming and interactive answers** — an answer can be the page catalogue's
  own parts (`frontend/src/lib/openui`, `docs/page-format.md`): `Text`, `Table`, `Chart`, `Steps`,
  `Callout`, `Cards`, `CodeBlock`; no `Diagram` or `Artifact` at first, as both need a second,
  slower call to draw. Plus `Sources` and `Proposal`, the tool card from above, on `onAction`.
  - The transport first, as `<Renderer :is-streaming>` is only the drawing half: a streaming
    method with tools on `LLM`, an async `POST /chat/stream` over SSE (`status`, `token`,
    `proposal`, `done`, `error`) and a frontend reading it with `fetch` (`EventSource` can't send
    the auth header).
  - Settle with a small test first how `Query()` and a `toolProvider` of real Kolmi reads behave.
  - If the OpenUI Lang doesn't parse, the answer shows as Markdown. The session keeps the source,
    to draw it again.

## After: new agents on the same base

Same tools, same loop, another trigger.

- [ ] **Report a bug in the app, watched by an agent** — for the app itself, to this repo's
  maintainer, not the teacher: a quiet link in Settings (not the sidebar — this is rare and
  technical), logged, judged by an agent before it becomes a real GitHub issue: genuine or a
  troll, how serious (no duplicate check against open issues yet, that needs read access and more
  context; skip it for a first cut). The same shape as the gatekeeper's pass (a row, an agent's
  verdict, the reason kept) — a discarded report is `Status` "discarded" in grey, not an error.
  Runs on the instance's own model key (the gatekeeper's), not the optional chat key, so it needs
  the same kind of daily cap per student the chat does, to keep spam cheap to shrug off. The
  backend holds the GitHub token (issues-write only, scoped to this repo); it never reaches the
  browser. One call that judges a report, no loop. Small and apart from the chat, so it can come
  earlier. Open: does a report also let its author see where it ended up, or is it
  fire-and-forget.
- [ ] **A forum** — one shared space for the class (not per page: a class is small, scattered
  threads get no traffic), for doubts and requests alike, not just notes. Kolmi is a participant
  in it, not a separate bolted-on checker: a role ("you are Kolmi, you help this class"), given
  the thread to read, free to judge for itself whether to step in (on being asked, or if no one
  human answers for a while) and, when it judges a thread genuinely reveals a content gap, free
  to propose a page through `write_page` — no category gate, no vote count standing in front of
  its judgment (see `AGENTS.md`). It's the chat's own loop and tools, woken by an event instead of
  a question: a new post, a mention, or an hourly check for threads with no human answer. The
  thread is its state, read again on every wake, so it needs no checkpointer. A thread it turns
  into a page shows that in place with `Status`, so whoever asked sees it was worth something.

## Also

- [x] **Take the notebook with you: export as Markdown** — any member downloads the class's
  shared pages as a zip, one `.md` per page, folders mirroring the tree and numbered in the
  admin's order (`GET /export`, optionally `?node_id=` for one section; `backend/app/export.py`).
  A quiet "Download this section" beside each section's title (the route also takes no section,
  for the whole notebook, which the nightly copy will use); a section's zip is what goes into a
  NotebookLM notebook for that topic (the free plan takes 50
  sources per notebook). Each file is the title, where the page sits and the page's Markdown, the
  source the notes agent writes, so only the layout is lost. Links to another page in the export
  are rewritten to its file; links and images that only meant something beside the notes' original
  files become plain text, so no file points at nothing. Only shared pages go out, never raw
  notes or attachments. Cost: nothing, no model is involved.
- [ ] **Export, the rest** — the same files with the page's data on top (title, description,
  order, date), so an import can read them back and a notes repo can keep them; a nightly copy
  into a private repo after the pass; students downloading their own raw notes; an admin switch
  to turn the export off. And fix at the source what the export has to patch: the notes agent
  copies links written for the notes' original files (60 of them across 24 pages in the test, 19
  matching another page by title), though it is told to link as `/node/<id>`.

## Later

- [ ] Moderation and reporting tools.
- [ ] More contribution types (links, images, files over the MCP).
- [ ] Notifications (weekly digest, "the hive worked", a forum reply).
- [ ] More languages beyond English and Spanish.
- [ ] Better interactive pieces, if pages turn out to need them.
- [ ] The OpenUI Gateway as the web model again, once its account has credit (only the key
  changes).

## Ideas, not committed

- A teacher dashboard (what the hive did this week).
- Export the notes to PDF.
- Link a topic to NotebookLM, so a section's notes can be studied there too.
