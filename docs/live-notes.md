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
  │   "A container is an isolated process..."      │
  │   4 following                           [Open] │
  └────────────────────────────────────────────────┘

Earlier
  Mon 6 Oct · Deployment · notes by Ana          [Open]
  Fri 3 Oct · Databases · notes by Luis          [Open]
```

- What's being written now comes first, with a live dot. When nothing is, a quiet line says so.
- "Start writing" opens a new note tied to the class the timetable says is on.
- Earlier sessions are listed by date and class, and can be reopened.

### One note, `/live/:id`

For someone watching:

```
Deployment class                     ● Live · 4 following
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
- The header carries the state, how many are following and a label saying the notes come from one
  person and nobody has checked them.

For the writer it is the editor, with a "Share live" switch (off by default) and an "End
session" button. Ending the session sends the text to the daily pass as an ordinary note. Later,
the suggestion chips appear under the paragraphs.

## Getting there

A sidebar entry, and a live dot on the timetable when a class has a note being written.

## Parts

Mostly elastic-ui parts that already exist: cards, `Status` for the live state, the editor Kolmi
already has. The blinking live dot may be missing; if so it is built in elastic-ui first.
