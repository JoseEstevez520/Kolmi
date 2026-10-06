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
  reorder, delete). The panel is three pages behind a selector: `/admin/content` (the tree),
  `/admin/people` and `/admin/class`; `/admin` goes to the content.
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

## Next: actions as tools, users and the MCP

One set of actions, used three ways: by the web, by the chat and by anyone's own AI through the
MCP. Reading is free; anything that changes something is confirmed (a button in the chat, the
client's own prompt over the MCP). The case that matters most: someone's AI reads their Moodle or
a GitHub repo and writes the class's notes in Kolmi.

- [x] **Actions as tools** — the base for everything below: one `invoke` every caller goes
  through (role, then params), `read_only`, `tool` and `mcp` on each action, descriptions and
  errors written for a model, a task-shaped `move_node`, light answers on the tool path, and
  where notes and the AI log came from. Nothing calls the tools yet: the MCP and the chat come
  next. See [docs/tools.md](docs/tools.md). Apply
  `supabase/migrations/20261006120000_sources.sql` in the Supabase SQL editor before deploying it.
- [x] **Pages from outside the pass** — admin only: `write_page(node_id, markdown, mode,
  source_url?)` (`replace` as it is, `merge` through the notes agent, which strips names and
  private data), `rebuild_page(node_id)`, `list_versions(node_id)` and `restore_version(version_id)`
  (confirmed). They run in the background, keep the version before and log who and from where.
  In the app, an admin opens a page's History in its top bar: its earlier versions, newest first,
  each restored after asking.
- [x] **An admin tool to edit a page's web** — `write_page_web` (admin, confirmed) sets a page's
  OpenUI Lang as written, with no web agent: checked against the catalogue first (each problem
  with its line and what to change), never leaving a page blank, the version before kept, logged
  with who and from where, and the Markdown left as it is. The web follows the Markdown. Any
  member's AI reads a page's web with `view_node`'s `include_web`. See
  [docs/tools.md](docs/tools.md). If a piece is missing, it goes into
  elastic-ui and the catalogue first.
- [x] **Users from the admin panel** — two roles, `student` and `admin`, and a status apart from
  the role (`active`, `pending`, `blocked`) in place of `approved`, checked once in `invoke` (and
  in the upload and export routes). An admin's users page, `/admin/people` (`list_users`, `set_role`,
  `set_status`, `delete_user`) and the class setting "New sign-ups need approval", with a waiting
  screen for whoever is pending or blocked; anyone changes their name and deletes their account in
  Settings. The first to sign up on an instance with no admin becomes one; the last active admin
  can't be demoted, blocked or deleted; losing access goes through `on_access_lost`, where the MCP
  will revoke tokens. A deleted account takes its notes' files from Storage and its account from
  Supabase Auth; the files on shared pages stay. Apply `supabase/migrations/20261007120000_users.sql`
  and `20261008120000_first_admin.sql` before deploying it. See
  [docs/authentication.md](docs/authentication.md).
- [ ] **Users, what's left** — two small things:
  - A blocked person with the app open sees the waiting screen only when they navigate; handle a
    blocking 403 in one place in the API client and send them there.
  - Drop the `approved` column in its own migration, once the status has run stable for a while.
- [x] **The MCP** — Kolmi as a server for anyone's own AI, in the same FastAPI at `/mcp`
  (streamable HTTP, the `mcp` Python SDK), so it stays one instance per class. See
  [docs/mcp.md](docs/mcp.md). Done, in a first batch:
  - Personal tokens (`api_tokens`, only the hash kept), shown once and revocable, made from the
    web; `get_context` takes a Supabase session or a `kolmi_...` token, which reaches only the
    MCP's tools on any route. `on_access_lost` revokes someone's tokens.
  - The registry's tools through `invoke`, per role (`read_only` as `readOnlyHint`,
    `requires_confirmation` as `destructiveHint`): a student reads the tree, pages and timetable,
    searches (`search_pages`) and creates, edits, lists and deletes their own notes (`delete_note`);
    an admin also writes pages, their web, versions, received notes, the AI log and `run_pass`,
    and shapes the tree and the timetable (users and settings stay in the app and the chat).
  - Notes through the MCP with `source = 'mcp'` and their `source_url`; a daily cap per student
    (`mcp_daily_notes`, 30), none for admins. Text only.
  - Apply `supabase/migrations/20261009120000_api_tokens.sql` before deploying it.

  - A second batch: the shared pages as resources (`kolmi://page/{id}`), the prompt
    `material_to_notes`, evals for the tools' descriptions (`backend/evals/`), and the Moodle +
    GitHub + Kolmi case in both READMEs.
- [x] **"Connect your AI" in Settings** — a named connection makes a token, shown once with the
  instructions for each kind of client (Claude Code, Gemini CLI, Codex CLI, any other: the address,
  the header and an `mcpServers` JSON) and a text to tell your agent; then the connections, with
  when each was last used, revocable. Left: the editors' install links (Cursor, VS Code) and
  Windsurf's JSON, once their official formats are checked.
- [ ] **Sign in over OAuth for chat apps** — the AI chat apps' custom connectors expect OAuth, not
  a pasted token: the address, then Kolmi's own sign-in in the browser. Comes right after the MCP
  if the class mostly uses chat apps rather than coding agents; check first whether Supabase Auth
  can be the OAuth server.
- [x] **How agents are built, in `AGENTS.md`** — agents use the OpenAI SDK with their own loop;
  one moves to LangGraph only when it must pause and resume its own reasoning, survive a long run
  or coordinate with other agents. Approval and state in the database are not reasons.

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
- [ ] **Tools in the chat** — the registry's tools for the caller's role. Backend done, the web's
  card missing.
  - Done: `ask_chat` offers the actions on surface `chat` for the asker's role. Reads run inside
    the model's loop (`tools.run_tool`). Anything that changes something is checked with
    `registry.check` and kept as a proposal in `chat_proposals`, not run; every write is a
    proposal, `create_note` included. `POST /chat/confirm` (only the asker, only once, edited
    args validated again, runs through `invoke`) and `POST /chat/cancel`. Evals:
    `backend/evals/chat_tools.json`, `python -m evals.run_chat_evals`. See
    [docs/tools.md](docs/tools.md).
  - Left: the proposal card (Confirm, Edit, Cancel) in elastic-ui, which has none yet (`ChatTool`
    has no actions); release it, bump `frontend/vendor/`, then build the web's side.
  - Before deploying, apply `supabase/migrations/20261010120000_chat_proposals.sql`.
  - What it's for: "make a note that the exam goes up to unit 4", "save what you just explained as
    a note", "why was my note from yesterday discarded?"; for an admin, "make a Kubernetes section
    with these three pages", "move Maven out of Spring Boot", "put this text as the CI/CD
    page", "go back to yesterday's Docker page", "what did last night's pass do?", "approve the
    three pending users".
- [x] **Real RAG: search by meaning, so it scales** — the chat no longer depends on the tree
  fitting in the model's context: a hybrid search finds the closest chunks and hands them over.
  - pgvector on Supabase: `page_chunks` (node, position, heading breadcrumb, text, a hash of the
    page's Markdown, `vector(1536)` embedding, a generated full-text column), an HNSW cosine index,
    a GIN one on the text and the `match_page_chunks` RPC: Supabase's hybrid search (full text and
    vectors, Reciprocal Rank Fusion). **Apply
    `supabase/migrations/20261010130000_page_chunks.sql` before deploying.**
  - Chunking (`app/rag/chunker.py`): over `content_md`, split at headings with markdown-it-py's
    tokens (a real CommonMark parser), so code fences and tables are whole blocks; a long section
    splits between blocks (~1500 characters). Looked at LangChain's `MarkdownHeaderTextSplitter`
    (line-based fences, no table awareness, its size pass cuts code) and LlamaIndex's
    `MarkdownNodeParser` (heavy, backticks only); neither fit.
  - Indexing (`app/rag/index.py`): at the end of the daily pass (only the pages it wrote), after
    `write_page`, `rebuild_page` and `restore_version`; not `write_page_web`. An unchanged hash is
    skipped, a deleted node takes its chunks by cascade, and a failure is logged, never fails a
    write. Reindex everything once with `python -m app.rag reindex` (`--force` ignores hashes).
  - Embeddings: any OpenAI-compatible endpoint (`EMBEDDING_API_KEY`, `EMBEDDING_BASE_URL`,
    `EMBEDDING_MODEL`, default `text-embedding-3-small`, $0.02 per 1M tokens). DeepSeek has none.
    Without the key the index stays empty and the chat and `search_pages` work as before.
  - The chat gets the closest chunks for the question with their page and heading, before the
    question; `read_page` stays for a whole page and the answer cites pages as before. With
    passages, the tree index keeps to 6,000 characters: past it, it drops the descriptions, then
    the pages (a section's are one `read_page` away).
  - `search_pages` (over the MCP) uses the same search, one result per page, same shape; plain
    word matching without an index. Hybrid because exact terms (a command, a class name) matter in
    class notes and pure vectors miss them.
  - Sources: Supabase's AI guides (semantic search, hybrid search, HNSW indexes) and OpenAI's
    embeddings model page.
- [ ] **A chat page** — `/chat` first, with the conversation wide, and `/chat/:sessionId` once sessions exist: sessions on the left (a `Sheet` on a phone),
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
- [ ] **Better pages** — some notes that would suit a drawing come out with none (a flow got a
  diagram, three beans sharing an instance did not); the pass can't read a PDF, a zip or a photo,
  so a file only gets judged by its name. Decide whether the Gateway's web model is worth
  bringing back.
- [ ] The page showing it is being rebuilt, while `write_page`, `rebuild_page` or the pass remake
  it. Needs a state per page and the web asking for it; today the new version just appears.
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
