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
4. Swap the tarball in `vendor/` and `package.json`.
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
"elastic-ui": "file:vendor/elastic-ui-0.4.2.tgz"
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
  status (pending / processed / discarded) as a label in its outcome colour. Long notes are
  kept to a few lines with a fading end and a "Show more", so one never dominates the list.
- **Section** (`/node/:id`, kind `section`): its children as a grid of cards, each opening
  its own node.
- **Page** (`/node/:id`, kind `page`): one page's title and its content, drawn from its OpenUI Lang
  (`docs/page-format.md`) or, without it, from its Markdown; an empty state
  when it has none.
- **Admin** (admins only): the whole node tree, each row editable in place (rename, edit,
  move, reorder) and deleted with a confirmation, with a section or a page added at any
  level. Below it, the class language: a `Select` in a `Field`, saved as soon as
  it's picked.

The content is one tree of nodes: a **section** groups, a **page** holds the content. The
sidebar lists only the top-level nodes, the one holding the current page lit; the rest is
reached from a section and the header's breadcrumbs, which give the path to the node, each
chevron opening the nodes at that level. A page ends with the previous and next nodes of
its section ("2 of 5"), and on wide screens shows a table of contents of its headings; a
link to `/node/<id>` in its text stays inside the app.

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
| `CardGrid` + `PageCard` | a grid of cards, one per node or note: a title and a text, and a footer with a date and a status label; a note's text is clamped with a fading end |
| `AdminNode` + `AdminRow` + the two dialogs | the recursive tree: one row (rename, move up/down, delete) and the dialogs that add a node or edit its description, icon, colour and `on_home` |
