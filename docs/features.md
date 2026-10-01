# Features and actions

An extension of what's already specified (login, notes and the nightly pass). Add a `role`
column to `profiles` (`student` | `admin`).

Pages are web content built from components (the app's current format, don't change it). The
AI writes them using the existing components.

## Content structure

Module → Sections (tabs) → Pages.

Example: "Programming" → "Class notes", "Extra" → pages.

For now all sections work the same.

## Features

### Admin (the only one with a management UI)

- A panel to create, rename, reorder (drag and drop) and delete modules, sections and pages.
- A log of what the AI did: on each pass, which notes it processed, which pages it created or
  changed, which notes it discarded (and why), and which pages the reviewer flagged as
  doubtful.
- A list of received notes.

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
- Permissions are checked **inside** each action, based on the calling user. The chat acts as
  that user and has no more powers than they do.
- Destructive actions carry `requires_confirmation: true` so the chat asks for confirmation
  before running them.
- Every change the AI makes to a page saves the previous version first and leaves an entry in
  the log (there's no restore from the UI for now).

## Actions

### All users

- `list_modules()`
- `view_section(section_id)`: with its list of pages
- `view_page(page_id)`
- `create_note(content, module_id, page_id?)`
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

- **Taking notes inside Kolmi**: replace the simple form with a comfortable, good-looking
  editor (Notion style: headings, lists, code, images) so students take their notes directly
  in the app during class. Those notes are sent as notes to the nightly pass.
  → Store the note content now so it can later take rich text (for example, a `content`
  column plus a `format` = `text`).
- A chat with AI that uses the actions as tools.
- RAG / search in the notes.
- Restore versions from the UI.
- Choose per section whether it's fed by notes or not.

## Out of scope

- A visual page editor for the admin (the AI writes the content).
- Changing the page format or the component system.
- Forums.
