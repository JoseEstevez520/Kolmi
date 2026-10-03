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
- [x] **Settings** — language and animations, kept in each browser. Animations stay on by
  default even when the system asks for reduced motion; the switch hands the choice back to
  the system.
- [x] **Faster pages** — the API checks the session against the project's signing keys
  instead of asking Supabase on every request, the tree is kept in the browser, and pages
  are read ahead when a link is pointed at.
- [x] **Pages in the class's language** — an admin picks the class language in the admin
  panel and the daily pass writes the shared notes and pages in it, whatever language each
  note came in. It's one row in a `settings` table; until that exists, `CLASS_LANGUAGE`
  decides (`en` by default). Apply
  [supabase/migrations/20261002120000_settings.sql](supabase/migrations/20261002120000_settings.sql)
  in the Supabase SQL editor to turn the control on.

## Now

- [ ] **Seed the tree** — the class's modules (DWCS, DIW, DWCC, Deployment, DASP) and Extra as
  sections, each with a description, so the gatekeeper knows where things go.
- [ ] **Import the existing notes** — the class repo's notes as pages: their Markdown as it is,
  and the web page made from it. Kolmi starts with real content, and it tests the web agent on
  about 40 real notes.
- [ ] **First real pass** — notes written in the app, the daily pass run on them, and the pages
  it writes checked on screen.
- [ ] **Deploy** — the instance on the server: Docker, the pass's host cron and the domain.

## Next

- [ ] **Downloadable files** — a page can carry files to download: zips, PDFs, code. Students
  can leave them with a note too, and they end up on the page they belong to.
  Open question: how students' files are handled (who checks them, size and type limits,
  what the pass does with them).
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
