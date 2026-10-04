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

## Now

- [ ] **Seed the tree** — the class's modules (DWCS, DIW, DWCC, Deployment, DASP) and Extra as
  sections, each with a description, so the gatekeeper knows where things go. The database is
  empty on purpose while the app is built: the real tree comes when it's ready for the class.
- [ ] **Import the existing notes** — the class repo's notes as pages: their Markdown as it is,
  and the web page made from it. Nothing is imported yet; it waits until the app is ready for
  the class.
- [x] **First real pass** — tried on 2026-10-03 with notes from the class repo, the Moodle and a
  classmate's photos, and then cleaned up. The gatekeeper did what the plan expects in every case
  (filler, repeat, wrong hint, a note merged into a page, new pages, files attached or discarded).
  The plan and the results are in [docs/testing.md](docs/testing.md).
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
- [ ] **Deploy** — the instance on the server: Docker, the pass's host cron and the domain.
- [ ] **Timetable: dragging onto an occupied slot** — today a dropped block just lands where it's
  let go, even over another one. The usual calendar feel is for what's already there to shift
  aside (or refuse the drop); decide which, and build it.

## Next

- [ ] **Chat with the notes (RAG)** — ask the hive; it answers citing the page, each page's
  Markdown its source. Two ways in, and a student's own key always wins:
  1. **The class's own key**, set by the admin in Settings (on/off, plus a daily message limit).
     Held server-side, since a shared limit can only be enforced there: a row per student per
     day, counted, blocked past the limit — the same shape as `ai_log`/`ai_passes`. No live cost
     metering, just a message count.
  2. **A student's own key**, kept only in their browser (as the language or animation setting
     already are) and called straight from there to the provider: it never touches the backend,
     so nothing to encrypt or hold. Any OpenAI-compatible endpoint, the same assumption the web
     model already makes (`docs/page-format.md`).
  A student's own key is used whenever they have one set, whatever the admin's key is doing
  (off, or its limit spent) — otherwise the class's, if the admin turned it on; otherwise the
  chat says it isn't available here. A plain request-response first; a loop or tool use (looking
  things up, not just the page it's asked about) is a LangGraph job (`AGENTS.md`), not the plain
  OpenAI SDK. Needs no room of its own: elastic-ui's `ChatMorph` is an orb mounted once in the
  app shell (beside `AppSidebar`), floating over every screen, open on any page without leaving
  it — `ChatThread` + `ChatComposer` + `ChatSources` for the citations, parts the library already
  has.
- [ ] **Report a bug in the app, watched by an agent** — for the app itself, to this repo's
  maintainer, not the teacher: a quiet link in Settings (not the sidebar — this is rare and
  technical), logged, judged by an agent before it becomes a real GitHub issue: genuine or a
  troll, how serious (no duplicate check against open issues yet, that needs read access and more
  context; skip it for a first cut). The same shape as the gatekeeper's pass (a row, an agent's
  verdict, the reason kept) — a discarded report is `Status` "discarded" in grey, not an error.
  Runs on the instance's own model key (the gatekeeper's), not the optional chat key, so it needs
  the same kind of daily cap per student the chat does, to keep spam cheap to shrug off. The
  backend holds the GitHub token (issues-write only, scoped to this repo); it never reaches the
  browser. Open: does a report also let its author see where it ended up, or is it fire-and-forget.
- [ ] **A forum** — one shared space for the class (not per page: a class is small, scattered
  threads get no traffic), for doubts and requests alike, not just notes. Kolmi is a participant
  in it, not a separate bolted-on checker: a role ("you are Kolmi, you help this class"), given
  the thread to read, free to judge for itself whether to step in (on being asked, or if no one
  human answers for a while) and, when it judges a thread genuinely reveals a content gap, free
  to call the same page-creation flow the gatekeeper already uses — no category gate, no vote
  count standing in front of its judgment (see the new rule in `AGENTS.md`). This is real
  tool-calling with a judgment call of its own, not a plain request-response, so it's LangGraph
  from the start (`AGENTS.md`), unlike the plain Q&A chat above. A thread it turns into a page
  shows that in place with `Status`, so whoever asked sees it was worth something.

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
