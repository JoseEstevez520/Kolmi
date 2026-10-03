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
- [x] **Notes first, then the page** — the notes agent writes the Markdown with the class repo's
  apuntes-claros skill; the web agent makes the page from it with apuntes-web; the main model
  draws the visuals.
- [x] **A richer page catalogue** — elastic-ui's own parts: charts, composed diagrams, tables,
  glossaries, diffs, code walkthroughs, terminal and agent replays, cards, logos, and pieces built
  from library parts in a sandboxed frame.
- [x] **Notes save themselves** — as you write, with no draft and no send button.
- [x] **The pass's schedule in the admin** — on or off, the times and the days (Madrid time),
  kept in `settings`; the host cron runs every hour with `--if-due` and the pass runs only when it
  is due. "Run now" starts it in the background, and the next run is shown.
- [x] **Where a new page goes** — the gatekeeper says where a new page sits among its siblings
  (first, after one, or last) and why; the reason shows in the AI log.
- [x] **Downloadable files** — a page can carry files to download: zips, PDFs, code. Students
  can leave them with a note too: the gatekeeper looks at each one and either attaches it to the
  page it belongs to or discards it, with its reason in the log. Up to 20 MB a file and 5 a
  note; no executables.

## Now

- [ ] **Seed the tree** — the class's modules (DWCS, DIW, DWCC, Deployment, DASP) and Extra as
  sections, each with a description, so the gatekeeper knows where things go. A test version is
  in place; the real one comes with the class's content.
- [ ] **Import the existing notes** — the class repo's notes as pages: their Markdown as it is,
  and the web page made from it. Three were imported as a test; the rest waits until the app is
  ready for the class.
- [ ] **First real pass** — notes written in the app, the daily pass run on them, and the pages
  it writes checked on screen.
- [ ] **Deploy** — the instance on the server: Docker, the pass's host cron and the domain.

## Next

- [ ] **Chat with the notes (RAG)** — ask the hive; it answers citing the page. It runs on the
  main model, and each page's Markdown is its source.
- [ ] **Status part** — a quieter way to show a note's or a pass's state (built in elastic-ui;
  see its roadmap), in place of the coloured badges.
- [ ] **Forums** — doubts and answers, not just notes.

## Later

- [ ] Moderation and reporting tools.
- [ ] More contribution types (links, images).
- [ ] Notifications (weekly digest, "the hive worked").
- [ ] More languages beyond English and Spanish.
- [ ] Better interactive pieces, if pages turn out to need them.
- [ ] The OpenUI Gateway as the web model again, once its account has credit (only the key
  changes).

## Ideas, not committed

- A teacher dashboard (what the hive did this week).
- Export the notes to Markdown/PDF.
- An MCP connection so an agent can read the class notes.
- Link a topic to NotebookLM, so a section's notes can be studied there too.
