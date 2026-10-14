# Live notes

A sketch, not a spec. Live notes let one person take notes during a class while the rest
watch them appear, to keep up when they get lost, miss a moment or aren't there. They sit next
to the notes, not in place of them. The steps and what's still open are in the
[roadmap](../ROADMAP.md).

## No screen of its own

Live notes are not another page. Writing live is a switch in the header of the note being
written; watching is a row on the Notes screen.

- **Writing.** In a note's header, an icon-only switch ("Share live", a radio icon). Turning it
  on makes a session linked to the note (its title and current text) and shares it with the
  class; from then on every save of the note also sends its text to the session. Turning it off
  ends the session. The note stays an ordinary note either way and still goes through the daily
  pass; the session is only its mirror. On a brand-new note the switch creates the note first.
  On reload the switch reads its state from the author's own open session whose `note_id` is
  that note.
- **One at a time.** A person has one open session. Turning the switch on in another note ends
  the previous session (the first note simply shows the switch off when reopened).
- **Watching.** On Notes, above "My notes", a row of compact cards, one per live note by someone
  else: the live ring, title, author and the end of the text. It appears only when there are
  any; no heading, no empty state. Your own live note is not in it. A card opens `/live/:id`,
  read-only, following the end of the text (a button stops following). The author opening their
  own `/live/:id` is sent to the note.
- **Who is following.** Reading a session, as anyone but its author, registers the reader for 15
  seconds (`FOLLOW_WINDOW`). `read_live_note` answers `followers` (id and name of active members,
  at most 20, with `followers_count` past that), also in the `unchanged` short answer, since the
  list changes while the text doesn't. It is kept in memory in the API process (one uvicorn), so
  no table: a restart empties it and the next poll refills it. The watcher's header and the
  writer's bar (which reads its own session every 6 s while the switch is on) show them as a small
  stack of initials, names on hover, nothing when nobody follows. Names are fine here, a social
  surface; they never go into pages.
- A session mirrors an ordinary note, so the note itself goes through the daily pass like any
  note. There is no separate step for ending a session.
- Ended sessions are not listed anywhere for now. Step 2 of the roadmap turns them into ordinary
  notes.

## Limits

A session ends by itself three hours after it started (`MAX_SESSION`): a class is not longer,
and a writer who forgot to end it must not stay live all day. The switch then shows off, and a
save that meets the ended session carries on quietly. A shared note also drops out of the row
when it hasn't been saved for five minutes; the note's page resends its text every two minutes.

## Parts

Only elastic-ui parts and the notes editor Kolmi already has: `PageCard` for the row, `Status`
(its `working` state, a turning arc) for "Live", a ghost `Button` for the switch, `Markdown`, `ConfirmButton`. No new
part was needed for step 1.

## Step 1, as built

- **Table** `live_notes`: `author_id`, `title`, a nullable `event_id` (the timetable slot on when
  it started), a nullable `note_id` (the author's note it mirrors;
  `20261014140000_live_notes_note_link.sql`), `content` (Markdown), `shared` (false by default),
  `ended_at`, `created_at`,
  `updated_at`. Migration `20261014120000_live_notes.sql`.
- **Who**: any active member starts, writes (their own session) and watches. A session nobody
  has shared is visible to its author only. Only the author saves or ends it; the author or an
  admin deletes it. One writer, last save wins.
- **"live"**: shared, not ended and saved in the last five minutes (`LIVE_WINDOW`). The writer's
  page resends the text every two minutes while it is shared, so a quiet stretch does not drop
  the note out of "live".
- **Actions** (`backend/app/actions/live_notes.py`): `start_live_note` (takes `note_id`, `title`, `content` and `shared`; the note must be the
  caller's, and starting ends any other open session of theirs), `save_live_note`,
  `end_live_note`, `delete_live_note` (not tools: the web saves every second or two) and
  `read_live_note`, `list_live_notes` (read-only, chat and MCP tools). `read_live_note` takes
  `since`, the `updated_at` the caller holds: if nothing changed it answers `{unchanged: true}`
  with the flags that can change on their own (`live`, `ended`). `list_live_notes` answers
  `{notes, current_class}`, the live ones first, each with a preview of its last 140 characters.
- **Chat**: on `/live/:id` the chat gets `live_id` and points the model at the note (see [chat.md](chat.md)); it reads it with `read_live_note`.
- **Web**: `/live/:id` for watching; the watcher polls every 4 s and the Notes row every 6 s,
  both stopping while the tab is hidden. The note's autosave (1.2 s after the last key) feeds
  the session.
