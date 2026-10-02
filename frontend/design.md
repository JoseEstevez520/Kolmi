# Design system

The app is built with [elastic-ui](https://github.com/JoseEstevez520/elastic-ui), José's Vue
component library. How it is used is in its `USAGE.md`: grey by default, one width, one thing
moving at a time, icons only where they help, no shadows of our own. This file only covers
what is Kolmi's.

**What is the library's and what is the app's**: how things look and behave is the library's.
What is said is the app's: the texts, the screens and the small pieces the app adds (the
sidebar, the page layout, the note cards). If something in the library breaks or is missing,
it is reported there and not patched over from here.

## elastic-ui

Installed from the packed library, `vendor/elastic-ui-0.3.3.tgz`, under the alias
`elastic-ui`:

```json
"elastic-ui": "file:vendor/elastic-ui-0.3.3.tgz"
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
  level.

The content is one tree of nodes: a **section** groups, a **page** holds the content. The
sidebar lists only the top-level nodes; the rest is reached from a section.

Login and Register sit in one `AuthLayout`: a card centred on the viewport, the Kolmi logo
above the wordmark "Kolmi" and the slogan "Learn as a hive.", the theme toggle in a corner.
Everything else lives inside the app shell: the sidebar, the page's own header with the theme
toggle, and only the content changing between pages.

## Layout pieces

| Piece | For |
|---|---|
| `AppSidebar` | Home, Notes, the top-level nodes with their icon and colour, the admin entry for admins and sign out, in elastic-ui's connected sidebar |
| `AuthLayout` | the centred card of Login and Register, with the mark and the theme toggle |
| `PageLayout` | one article at a single width, with its title and lead line |
| `CardGrid` + `PageCard` | a grid of cards, one per node or note: a title and a text, and a footer with a date and a status label; a note's text is clamped with a fading end |
| `AdminNode` + `AdminRow` + the two dialogs | the recursive tree: one row (rename, move up/down, delete) and the dialogs that add a node or edit its description, icon, colour and `on_home` |
