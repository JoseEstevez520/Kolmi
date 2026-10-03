# Testing the app with real cases

The app is built and the database is empty on purpose. This is the plan for trying it with real
material before the class uses it. What gets created while testing is test data, and it is
deleted afterwards.

## Where the real cases are

| Source | Where | What it gives |
|---|---|---|
| The class repo (ies-teis-daw2) | `<notes-repo>` (`modulos/`, `extra/`, 63 `.md` files) | Finished notes, and the style the pages should reach. Also its skills in `.agents/skills/` (apuntes-claros, apuntes-web). |
| The Moodle (Aula Virtual) | The token is in that repo's `.env` (`MOODLE_URL`, `MOODLE_TOKEN`); how to call it is in `extra/herramientas/moodle-api.md` there | A course's real contents: topics, examples, assignments and their solutions. `core_course_get_contents` with a course id. |
| A classmate's handwritten notes | `<downloads>/handwritten-notes/` (8 photos, `.jpg`) | A raw, messy contribution: photos with no text. |

Courses (from `core_enrol_get_users_courses`): [course ids removed].
In the virtual classroom "DAW" is *Despregamento de Aplicacións Web*, not a separate subject.

## How to run it

```bash
# backend (API on :8000) and frontend (:5173)
cd backend && .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
cd frontend && npm run dev
```

- The backend reads `backend/.env`: Supabase, the main model (`LLM_*`, DeepSeek, `deepseek-v4-pro`),
  the optional web model (`WEB_*`, left empty because the OpenUI Gateway's account has no
  credit, so the main model writes the pages) and `SUPABASE_DB_URL` for migrations.
- Backend tests: `cd backend && .venv/bin/python -m pytest -q` (153 pass).
- The pass: `python -m app.passes.daily --dry-run` writes nothing and asks only the gatekeeper;
  `--if-due` runs when the admin's schedule says so; "Run now" in Admin starts it in the
  background.
- To look at the logged-in screens without typing a password, use the dev browser profile
  described in `LOCAL.md` (gitignored).
- Migrations are in `supabase/migrations/`; all are applied to the project.

## What to test

### 1. A walk through the app (no model, costs nothing)

Light and dark, a wide screen and a phone width (390 px). Look for layout jumps, untranslated
text, borders that don't belong, and console errors.

- Home, notes list, the editor, Admin (tree, add and edit dialogs, class language, pass
  schedule), AI log, Settings (language list, animations switch).
- Navigation: breadcrumbs and their chevrons, the sidebar tab staying on the section, the
  table of contents, previous and next, an internal link, a deleted page.
- The editor: autosave status, "Where does it go?", attaching a file (button, drop, paste),
  zen mode.

### 2. A small test tree

Create a few sections with a short description each (what the gatekeeper reads), for example
DWCS, DIW and Despregamento, with no pages. Keep it small.

### 3. Notes that each test one decision

Write them from the real material above, as a student would, in different shapes:

1. A note that fits an existing page. First put one page in (a class note from the repo), then
   a note that adds something to it. Expected: the page is updated and nothing is lost.
2. A repeat: a note that says what a page already says. Expected: discarded, with a reason that
   quotes the page.
3. A new topic. Expected: a new page in the right section, placed where it belongs (first,
   after one, or last), with the reason in the log.
4. A wrong hint: pick the wrong place in "Where does it go?". Expected: the note is moved to
   where it belongs.
5. A note with a file, such as a zip or a PDF from the Moodle's examples. Expected: the
   gatekeeper attaches it to the page it belongs to or discards it with a reason, and the page
   shows it under "Downloads".
6. Only files: the classmate's photos. Expected: they are judged on their own and no page is
   rewritten. The photos are images with text in them and the pass can't read them yet, so this
   shows what it does with what it can't read.
7. Filler, like "hoy aprendí cosas". Expected: discarded.
8. A messy note in the style of the handwritten ones, typed from one of the photos. Expected:
   it comes out in the class's style without losing what it says.

### 4. The first real pass

"Run now" in Admin, then read, in this order:

- The AI log: what the gatekeeper decided for each note and why, and which pages it read.
- The pages: compare each with the hand-made one on the class site, with the questions the
  skills ask. Is there little text? A sentence before each piece? Is anything essential
  hidden? One colour per concept, a "To explore" section, readable in dark mode?
- Placement: where each new page sits among its siblings.
- Visuals: whether the charts and diagrams read well. Interactive pieces are rare, and that is
  fine.
- Cost and time: how long a pass takes and what it spends.

### 5. Real cases from the Moodle

Use a course's contents the way a student would. Take a topic's theory and examples (`Tema 3:
Controladores y Vistas`, `Tema 4: Servicios`) and its assignments, write notes from them and
compare the pages with the hand-made ones. Don't paste an assignment's solutions as if they
were notes.

## What to decide after testing

- Whether the gatekeeper's judgement is good enough, or its prompt needs a line.
- Whether pages reach the class site's level, and which pieces the models use too little.
- Whether the Gateway (a stronger web model) is worth bringing back.
- What the pass costs per night, to set the schedule and the model.

## Known limits

- Images are stored and judged by name, type and size; their content is not read.
- The OpenUI Gateway has no credit: pages are written by the main model.
- Interactive pieces are rare unless the notes ask for one.
- Files of a deleted note or page stay in Storage until deleted by hand.
- Nothing runs on a server yet: the Docker image, compose file and hourly cron are written
  (`backend/README.md`) but not deployed.

## Cleaning up

Test content is deleted afterwards. The accounts (`profiles`) and `settings` stay: deleting the
accounts would lock the admin out. The order that works: the files in Storage first, then `ai_log`, `files`, `node_versions`,
`notes`, `ai_passes` and `nodes`.
