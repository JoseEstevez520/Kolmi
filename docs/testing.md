# Testing the app with real cases

The plan for trying an instance with real material before its class uses it. What gets created
while testing is test data, and it is deleted afterwards. Where an instance's own material lives
(its notes, its courses, its paths) is personal setup and goes in `LOCAL.md`, never here.

## Where real cases come from

| Source | What it gives |
|---|---|
| A set of finished notes (a class's own notes repo, say) | Notes as the pages should end up, and a style to reach. |
| The school's learning platform | A course's real contents: topics, examples, assignments. |
| Photos of handwritten notes | A raw, messy contribution: images with no text. |

## How to run it

```bash
# backend (API on :8000) and frontend (:5173)
cd backend && .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
cd frontend && npm run dev
```

- The backend reads `backend/.env`: Supabase, the main model (`LLM_*`), the optional web model
  (`WEB_*`; left empty, the main model writes the pages) and `SUPABASE_DB_URL` for migrations.
- Backend tests: `cd backend && .venv/bin/python -m pytest -q`.
- The pass: `python -m app.passes.daily --dry-run` writes nothing and asks only the gatekeeper;
  `--if-due` runs when the admin's schedule says so; "Run now" in Admin starts it in the
  background.
- Migrations are in `supabase/migrations/`.

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

Create a few sections with a short description each (what the gatekeeper reads), with no
pages. Keep it small.

### 3. Notes that each test one decision

Write them from the real material above, as a student would, in different shapes:

1. A note that fits an existing page. First put one page in, then a note that adds something
   to it. Expected: the page is updated and nothing is lost.
2. A repeat: a note that says what a page already says. Expected: discarded, with a reason that
   quotes the page.
3. A new topic. Expected: a new page in the right section, placed where it belongs (first,
   after one, or last), with the reason in the log.
4. A wrong hint: pick the wrong place in "Where does it go?". Expected: the note is moved to
   where it belongs.
5. A note with a file, such as a zip or a PDF of a course's examples. Expected: the gatekeeper
   attaches it to the page it belongs to or discards it with a reason, and the page shows it
   under "Downloads".
6. Only files: photos of handwritten notes. Expected: they are judged on their own and no page
   is rewritten. The pass can't read images yet, so this shows what it does with what it can't
   read.
7. Filler, like "hoy aprendí cosas". Expected: discarded.
8. A messy note in the style of the handwritten ones, typed from one of the photos. Expected:
   it comes out in the class's style without losing what it says.

### 4. The first real pass

"Run now" in Admin, then read, in this order:

- The AI log: what the gatekeeper decided for each note and why, and which pages it read.
- The pages: compare each with a hand-made one. Is there little text? A sentence before each
  piece? Is anything essential hidden? One colour per concept, a "To explore" section, readable
  in dark mode?
- Placement: where each new page sits among its siblings.
- Visuals: whether the charts and diagrams read well. Interactive pieces are rare, and that is
  fine.
- Cost and time: how long a pass takes and what it spends.

### 5. A course's real contents

Use a course's contents the way a student would: take a topic's theory, examples and
assignments, write notes from them and compare the pages with hand-made ones. Don't paste an
assignment's solutions as if they were notes.

## What the first rounds showed

Two rounds, in October 2026: a few notes over three passes, then a real tree and 23 notes over
three simulated nights, which made 14 pages.

- **Gatekeeper:** every call was right. Filler and repeats were discarded (quoting the page), a
  wrong hint was moved, a false fact was discarded saying so, a note on two topics was split
  between two pages, an addition was merged without losing anything, new pages got a place and
  a reason, and zips and PDFs went under "Downloads". A photos-only note was discarded, as the
  pass can't read images. It isn't deterministic: the same notes were one page in a dry run and
  two in the real pass.
- **Pages:** tables, code, callouts, steps, links between pages and previous/next read well in
  light and dark and on a phone. They keep almost all the code and terms of their notes in about
  half the words. Figures appeared on about half the pages: a flow got a diagram, three beans
  sharing one instance got a list and code. Few pages had a "To explore" section. The pass's
  `visuals` list only counts what the main model draws afterwards, so a diagram made of the
  library's parts doesn't show there. Figures fade in as they scroll into view, so a full-page
  screenshot shows them as empty boxes.
- **Links:** a note's "To explore" links were sometimes dropped by the notes agent, though the
  gatekeeper's summary kept them.
- **A learning platform's courses** often hold their theory only in zips and PDFs, so there is
  little text to write notes from.
- **Time:** 1.5 to 5.5 minutes for 2 to 8 notes, about 1.5 minutes per new page, so a night
  with 30 notes is a pass of half an hour or more. Fine for a cron, not for "Run now" with a
  class waiting. The cost in money hasn't been measured.

### Why did it do that?

The notes agent ends its answer with `---decisions---` and a few lines on what it left out, merged
or changed from the material and why. Kolmi cuts them off the page and keeps them in the pass's
stats (`pages[].decisions`). When a page isn't what you expected, read them first.

## What to decide after testing

- Whether the gatekeeper's judgement is good enough, or its prompt needs a line.
- Whether pages reach the level of hand-made ones, and which pieces the models use too little.
- Whether a stronger web model is worth it.
- What the pass costs per run, to set the schedule and the model.

## Known limits

- Images are stored and judged by name, type and size; their content is not read.
- Interactive pieces are rare unless the notes ask for one.
- Files of a deleted note or page stay in Storage until deleted by hand.

## Cleaning up

Test content is deleted afterwards. The accounts (`profiles`) and `settings` stay: deleting the
accounts would lock the admin out. The order that works: the files in Storage first, then
`ai_log`, `files`, `node_versions`, `notes`, `ai_passes` and `nodes`.
