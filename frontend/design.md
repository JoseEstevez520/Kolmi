# Design system

The app is built with [elastic-ui](https://github.com/JoseEstevez520/elastic-ui), José's Vue
component library. How it is used is in its `USAGE.md`: grey by default, one width, one thing
moving at a time, icons only where they help, no shadows of our own. This file only covers
what is Kolmi's.

**What is the library's and what is the app's**: how things look and behave is the library's.
What is said is the app's: the texts, the screens, and how they put the library's parts
together (the sidebar, the page layout, the note cards).

**When something is missing, it is built in the library.** A piece no screen can compose from
existing parts, a missing variant (a ghost trigger, say) or a bug is made in elastic-ui, not
here: no hand-styled stand-ins, no overriding its classes. The steps:

1. Plan it in the elastic-ui repo, following its `AGENTS.md` and `DECISIONS.md`.
2. Build it with its story and its `USAGE.md` entry.
3. Release a version and pack it.
4. Swap the tarball in `vendor/` and point `frontend/package.json` and `landing/package.json` at it;
   `npm install` in both refreshes their lockfiles.
5. Restart the dev server: a reload keeps the old version.

**A fading edge only when the text runs past.** `mask-fade-r` always fades a line's end,
whether it fits or not, so a short label loses its last letters. Put a line that may not fit in
elastic-ui's `TruncatedText`, which fades only while it runs past (`AdminRow`, the admin log's
tables). Never use the bare class on text.

The page catalogue (`src/lib/openui/`) follows the same rule. Each component the AI may write
maps to a library part, and its renderer only passes the props on.

## elastic-ui

Installed from the packed library, `vendor/elastic-ui-<version>.tgz`, under the alias
`elastic-ui`:

```json
"elastic-ui": "file:vendor/elastic-ui-0.7.1.tgz"
```

It ships no compiled CSS: `src/style.css` imports its tokens and points Tailwind at its
components with `@source`. The library's own texts (screen-reader names, "On this page"…) are
in English by default, so the app does not override them.

## Colour

Grey by default. `--color-accent` in `src/style.css` is the same near-black as the text
(near-white in the dark theme): the app has no accent colour. Colour only carries meaning:
the outcomes (success, warning, danger) and the aurora, which is the library's and does not
appear in phase 1.

## Screens

- **Login**: "Sign in with Google", an email and password form, and links to Sign up and
  Forgot my password.
- **Register**: the class code and a display name, prefilled from the Google account when
  there is one. Arriving from "Sign up" with no account yet, it asks for email and password
  too.
- **Home** (`/`): the class name and a grid of cards for the nodes marked "on the home".
- **Notes**: a text box to leave a note and a grid of "my notes", each with its date and its
  status (pending / processed / discarded) as a `Status`: a ring whose icon carries the colour. Long notes are
  kept to a few lines with a fading end and a "Show more", so one never dominates the list.
- **Section** (`/node/:id`, kind `section`): its children as a grid of cards, each opening
  its own node.
- **Page** (`/node/:id`, kind `page`): one page's title and its content, drawn from its OpenUI Lang
  (`docs/page-format.md`) or, without it, from its Markdown; an empty state
  when it has none.
- **Files**: a page ends with a "Downloads" section, drawn by the app (never by the AI): a
  card per file, with its icon, name and size. An admin adds them from the page's Edit dialog;
  a student attaches them to a note from a quiet "Attach" button in the editor's top bar, which
  opens a panel (`PopoverMorph`) with a `FileUpload compact`; dragging a file anywhere over the
  editor (`FileDropZone`) or pasting one does the same. Attaching works before anything is
  written: the first file creates the note, so a note may hold only files. The admin dialog uses
  the default `FileUpload`.
- **Admin** (admins only): the whole node tree, each row editable in place (rename, edit,
  move, reorder) and deleted with a confirmation, with a section or a page added at any
  level. Below it, the class language: a `Select` in a `Field`, saved as soon as
  it's picked; and when the daily AI pass runs: the days in a `WeekPillbox`, the times on a
  `DayStrip`, saved as soon as they are settled.

The content is one tree of nodes: a **section** groups, a **page** holds the content. The
sidebar lists only the top-level nodes, the one holding the current page lit; the rest is
reached from a section and the header's breadcrumbs, which give the path to the node, each
chevron opening the nodes at that level. A page ends with the previous and next nodes of
its section ("2 of 5"), and on wide screens shows a table of contents of its headings; a
link to `/node/<id>` in its text stays inside the app.

## Guided tour

A new account sees a short tour once (`HomeView`'s `offerTour`, kept in this browser as the
other settings are; a row in Settings brings it back). It is elastic-ui's `Tour`: a ring and a
card that travel between the real screens, not just their sidebar links — Home, Notes' "New
note", Admin (admins only) and Settings, each `TourStep`'s `to` sending the app there first
(`App.vue`'s `goToStep`) before it is measured.

Login and Register sit in one `AuthLayout`: a card centred on the viewport, the Kolmi logo
above the wordmark "Kolmi" and the slogan "Learn as a hive.", the theme toggle in a corner.
Everything else lives inside the app shell: the sidebar, the page's own header with the theme
toggle, and only the content changing between pages.

## Layout pieces

| Piece | For |
|---|---|
| `AppSidebar` | Home, Notes, the top-level nodes with their icon and colour, the admin entry for admins and sign out, in elastic-ui's connected sidebar |
| `AppBreadcrumbs` | the header's `Breadcrumbs`, from the tree, with each level's siblings |
| `PageNav` | a page's previous and next in its section, as linked `Card`s |
| `AuthLayout` | the centred card of Login and Register, with the mark and the theme toggle |
| `PageLayout` | one article at a single width, with its title and lead line; with `toc`, a `TableOfContents` of its headings at 2xl |
| `CardGrid` + `PageCard` | a grid of cards, one per node or note: a title and a text, and a footer with a date and a status; a note's text is clamped with a fading end |
| `AdminNode` + `AdminRow` + `NodeMark` + the two dialogs | the recursive tree inside a `TreeDrag`: one row, quiet at rest (a mark, which folds a section, and the title), with its add, edit and delete coming in when it is pointed at or focused; rows are moved by dragging them (the others make room) or with Alt and the arrows. The dialogs add a node or edit its description, icon and colour (one `IconPicker` field) and `on_home`. A node without an icon of its own shows elastic-ui's `FolderIcon` or `FileIcon`, tinted in its colour (`NodeMark` where a section's open state matters, `defaultMark` elsewhere, such as the sidebar) |

## Images and handouts

An image made for Kolmi (a poster, a handout, a card for the class chat) is built from the same
library, the same tokens and the app's own texts, with the Aurora as its one decoration. The
recipe, with the class invitation as the example, is in
[docs/brand-visuals.md](../docs/brand-visuals.md).

