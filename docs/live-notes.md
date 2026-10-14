# Live notes

A sketch, not a spec. Live notes let one person take notes during a class while the rest
watch them appear, to keep up when they get lost, miss a moment or aren't there. They sit next
to the notes, not in place of them. The steps and what's still open are in the
[roadmap](../ROADMAP.md).

## Two screens

### The list, `/live`

```
Live notes                                    [ Start writing ]

● Now
  ┌────────────────────────────────────────────────┐
  │ ● Deployment class             Ana · 2 min ago │
  │   "...A container is an isolated process..."   │
  └────────────────────────────────────────────────┘

Earlier
  Mon 6 Oct · Deployment · notes by Ana          [Open]
  Fri 3 Oct · Databases · notes by Luis          [Open]
```

- What's being written now comes first, with a live dot. When nothing is, a quiet line says so.
- "Start writing" asks for a title, offered from the class the timetable says is on, and opens
  a new note tied to that class.
- Earlier sessions are listed by date and class, and can be reopened.

### One note, `/live/:id`

For someone watching:

```
Deployment class                              ● Live
Notes by Ana · not checked

  Docker and containers
  A container is an isolated process that shares the
  host's kernel...

  - Image vs container
  - Layers
  ▌                          ← being typed right now
```

- Read-only. It follows the end of the note while it's written, and a button stops following so
  you can reread something.
- The header carries the state and a label saying the notes come from one person and nobody has
  checked them. (How many are following comes later.)

For the writer it is the editor, with a "Share live" switch (off by default) and an "End
session" button. Later, ending the session will send the text to the daily pass as an ordinary
note, and the suggestion chips will appear under the paragraphs.

## Limits

A session ends by itself three hours after it started (`MAX_SESSION`), shared or not: a class is
not longer, and a writer who forgot to end it must not stay live all day. A shared note also
drops out of "Now" when it hasn't been saved for five minutes.

## Getting there

A quiet icon beside "New note" on the Notes screen (live notes are notes, so no sidebar entry of
their own). A live dot on the timetable when a class has a note being written
is still to do.

## Parts

Only elastic-ui parts and the notes editor Kolmi already has: `PageCard` for the list, `Status`
(its `working` state, a turning arc) for "Live", `Switch`, `Markdown`, `ConfirmButton`. No new
part was needed for step 1.

## Step 1, as built

- **Table** `live_notes`: `author_id`, `title`, a nullable `event_id` (the timetable slot on when
  it started), `content` (Markdown), `shared` (false by default), `ended_at`, `created_at`,
  `updated_at`. Migration `20261014120000_live_notes.sql`.
- **Who**: any active member starts, writes (their own session) and watches. A session nobody
  has shared is visible to its author only. Only the author saves or ends it; the author or an
  admin deletes it. One writer, last save wins.
- **"Now"**: shared, not ended and saved in the last five minutes (`LIVE_WINDOW`). The writer's
  page resends the text every two minutes while it is shared, so a quiet stretch does not drop
  the note out of "Now".
- **Actions** (`backend/app/actions/live_notes.py`): `start_live_note`, `save_live_note`,
  `end_live_note`, `delete_live_note` (not tools: the web saves every second or two) and
  `read_live_note`, `list_live_notes` (read-only, chat and MCP tools). `read_live_note` takes
  `since`, the `updated_at` the caller holds: if nothing changed it answers `{unchanged: true}`
  with the flags that can change on their own (`live`, `ended`). `list_live_notes` answers
  `{notes, current_class}`, the live ones first, each with a preview of its last 140 characters.
- **Web**: `/live` and `/live/:id`; the watcher polls every 4 s and the list every 6 s, both
  stopping while the tab is hidden. Saving is debounced by one second.
