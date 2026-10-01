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

## Now

- [ ] **Daily pass** — a cron wakes the agent team (gatekeeper → notes → web) once a day, with
  a log and page versions. This is what fills the pages from the notes.
- [ ] **Page format** — source is OpenUI Lang (catalog plus a sandboxed escape-hatch artifact
  for new visuals and interactive widgets), rendered with `@openuidev/vue-lang`; Markdown is
  derived for the RAG. Generated through the Thesys C1 API.
- [ ] **Router and model choice** — a planner picks the model (OUI-1 for catalog pages,
  DeepSeek for complex ones) and catalog vs escape. Evaluate OUI-1 against DeepSeek on the
  same briefs; keep the winner as default and the other as fallback.

## Next

- [ ] **Notes editor** — a clean, minimalist editor (headings, lists, code) so students take
  their notes right in the app, instead of a plain text box. Rich-text ready (`notes.format`).
- [ ] **Chat with the notes (RAG)** — ask the hive; it answers citing the page.
- [ ] **Forums** — doubts and answers, not just notes.

## Later

- [ ] Moderation and reporting tools.
- [ ] More contribution types (links, files, images).
- [ ] Notifications (weekly digest, "the hive worked").
- [ ] Multi-language UI.

## Ideas, not committed

- A teacher dashboard (what the hive did this week).
- Export the notes to Markdown/PDF.
- An MCP connection so an agent can read the class notes.
