# Features and actions

An extension of what's already specified (login, notes and the pass). Add a `role`
column to `profiles` (`student` | `admin`).

The AI writes each page twice: first the Markdown, then the page itself as OpenUI Lang, made
from that Markdown (see [Page format](#page-format)).

## Content structure

Module → Sections (tabs) → Pages.

Example: "Programming" → "Class notes", "Extra" → pages.

For now all sections work the same.

## Page format

The source is **OpenUI Lang** (Thesys' open standard for generative UI): a compact, streaming,
declarative format where every line is `id = Component(args)`. It can hold catalog components
*and* a sandboxed escape-hatch component, so a page can carry a brand-new diagram or an
interactive widget. It's data, not compiled code, so the chat can reuse it too.

The **Markdown is the source**. The notes agent writes it first, and the web agent makes the
page from it. New notes are merged into the Markdown and the page is made again, which is
easier than editing OpenUI Lang. If the web model fails, the page keeps its last good version
or shows its Markdown. The RAG and the page versions read the Markdown too.

- The catalog comes from elastic-ui (`Prose`, `CodeBlock`, `Callout`, `Diagram`…), and the
  system prompt is generated from it with `@openuidev/cli`.
- The **escape hatch**: one catalog component (an artifact) whose prop is self-contained
  HTML/SVG/JS, rendered in a sandboxed iframe, for what the catalog doesn't cover.
- The frontend renders it with `@openuidev/vue-lang`.
- Written by an optional web model (any OpenAI-compatible endpoint, such as the OpenUI
  Gateway, which validates and repairs the output), with the main model (DeepSeek) taking over
  when it fails. Details in [page-format.md](page-format.md).

### Router

A planner decides, per page, two things:

- **Which model**: a cheap, fast one for a standard page (OUI-1 was the plan, but it isn't on
  the Gateway; `google/gemini-3.7-flash` is the default today); a stronger general model
  (DeepSeek) for anything complex (new diagrams, interactive components).
- **Catalog or escape**: compose the existing components, or reach for the sandboxed artifact.

The router is what keeps normal pages cheap while still letting the hard ones exist.

## Features

### Admin (the only one with a management UI)

- A panel to create, rename, edit, move, reorder (up and down) and delete sections and pages.
- A log of what the AI did: on each pass, which notes it processed, which pages it created or
  changed, which notes it discarded (and why), and which pages the reviewer flagged as
  doubtful.
- A list of received notes.
- The class language: the one the AI writes the shared notes and pages in. Notes in other
  languages still count, and their content ends up written in this one. It's separate from
  each person's UI language.

### Students

- Read modules, sections and pages.
- Leave notes with a simple text form (choosing a module and, optionally, a page).
- See their notes and their status (pending / processed / discarded).

## Architecture: everything is an action

- Every feature is implemented **once** as a backend action, with a name, a description,
  parameters with a schema (Pydantic) and a permission check.
- A **single registry** of actions, from which two things are generated:
  1. the API routes the web uses;
  2. the tools (function calling, OpenAI/DeepSeek format) for the future chat.
- Permissions are checked once, in `invoke`, for every caller (the web, the chat, the MCP); checks
  that depend on the data (whose note, whose file) stay in the action. The chat acts as that
  user and has no more powers than they do. How actions become tools:
  [tools.md](tools.md).
- Destructive actions carry `requires_confirmation: true` so the chat asks for confirmation
  before running them.
- Every change the AI makes to a page saves the previous version first and leaves an entry in
  the log (there's no restore from the UI for now).

## Actions

### All users

- `list_modules()`
- `view_section(section_id)`: with its list of pages
- `view_page(page_id)`
- `create_note(content, format?, node_id?)`: `node_id` is where the student thinks the note
  goes, a hint for the gatekeeper. It must be an existing section or page.
- `update_note(note_id, content, format?, node_id?)` — only your own note, while it is pending.
  Left out, the hint stays; `null` clears it.
- `my_notes(status?)`

### Admin only

- `create_module(name)` / `rename_module` / `reorder_modules` / `delete_module`\*
- `create_section(module_id, name)` / `rename_section` / `reorder_sections` / `delete_section`\*
- `create_page(section_id, title)` / `rename_page` / `delete_page`\*
- `list_notes(status?, module_id?)`
- `view_ai_log(pass_id?, since?)`
- `run_pass()`: runs the AI pass without waiting for the night
- `deactivate_user(user_id)`\*

(\*) requires confirmation.

## Future (don't build now, but don't close the door)

- **Images in notes**: the editor takes headings, lists, checklists, code and tables; images
  need a place to store the files first.
- A chat with AI that uses the actions as tools.
- RAG / search in the notes.
- Restore versions from the UI.
- Choose per section whether it's fed by notes or not.

## Out of scope

- A visual page editor for the admin (the AI writes the content).
- Forums.
