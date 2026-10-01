# Roadmap

What we're building and what's next. Open to whatever the class needs.

## Now

- [ ] **Frontend (clean)** — Vue 3 + Vite + elastic-ui, fresh (not the class web base).
  Screens: login, register (class code + name), leave a note, my notes.
- [ ] **Auth and users** — backend actions done; finish Supabase (Google, email) and wire the
  screens. Spec: [docs/authentication.md](docs/authentication.md).
- [ ] **Notes** — leave a note and list "my notes" (backend action done; frontend pending).
- [ ] **Content structure and admin panel** — modules → sections → pages, with admin CRUD and
  drag-and-drop reorder.

## Next

- [ ] **Daily pass** — a cron wakes the agent team (gatekeeper → notes → web) once a day, with
  a log and page versions.
- [ ] **Page format** — source is OpenUI Lang (catalog plus a sandboxed escape-hatch artifact
  for new visuals and interactive widgets), rendered with `@openuidev/vue-lang`; Markdown is
  derived for the RAG. Generated through the Thesys C1 API.
- [ ] **Router and model choice** — a planner picks the model (OUI-1 for catalog pages,
  DeepSeek for complex ones) and catalog vs escape. Evaluate OUI-1 against DeepSeek on the
  same briefs; keep the winner as default and the other as fallback.
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
