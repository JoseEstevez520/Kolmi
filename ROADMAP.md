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
  rendered over elastic-ui with `@openuidev/vue-lang`; Markdown is derived for the RAG. The web
  agent calls OpenUI Gateway and falls back to DeepSeek writing Markdown. See
  [docs/page-format.md](docs/page-format.md).

## Now

- [ ] **Page format live** — the Gateway answers `429` (the Thesys organisation's billing is
  suspended), so every page is Markdown for now. Unblock it and run a real pass end to end.
  Load the page renderer lazily so it leaves the main bundle.
- [ ] **Router and model choice** — a planner picks the model and catalog vs escape. OUI-1 is
  not on the Gateway, so compare the Gateway's models (`google/gemini-3.7-flash` by default)
  against DeepSeek on the same briefs; keep the winner as default and the other as fallback.

## Next

- [ ] **Spanish UI** — the interface in Spanish as well as English, picked by the browser's
  language with a switch in the app. All strings go through one i18n layer (Vue I18n or
  similar), and the AI writes the pages in the class's language.

- [ ] **Notes editor** — a clean, minimalist editor (headings, lists, code) so students take
  their notes right in the app, instead of a plain text box. Rich-text ready (`notes.format`).
- [ ] **Chat with the notes (RAG)** — ask the hive; it answers citing the page.
- [ ] **Forums** — doubts and answers, not just notes.

## Later

- [ ] Moderation and reporting tools.
- [ ] More contribution types (links, files, images).
- [ ] Notifications (weekly digest, "the hive worked").
- [ ] More languages beyond English and Spanish.

## Ideas, not committed

- A teacher dashboard (what the hive did this week).
- Export the notes to Markdown/PDF.
- An MCP connection so an agent can read the class notes.
