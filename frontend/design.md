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
- **Notes**: a text box to leave a note and a grid of "my notes", each with its date and its
  status (pending / processed / discarded) as a label in its outcome colour.
- **Section**: the pages of a section as a grid of cards, each opening its page.
- **Page**: one page's title and its Markdown; an empty state when it has none.
- **Admin** (admins only): the module → section → page tree, each row editable in place, moved
  up or down and deleted with a confirmation.

Login and Register sit in one `AuthLayout`: a card centred on the viewport, the Kolmi logo
above the wordmark "Kolmi" and the slogan "Learn as a hive.", the theme toggle in a corner.
Everything else lives inside the app shell: the sidebar, the page's own header with the theme
toggle, and only the content changing between pages.

## Layout pieces

| Piece | For |
|---|---|
| `AppSidebar` | the modules and their sections, the admin entry for admins and sign out, in elastic-ui's connected sidebar |
| `AuthLayout` | the centred card of Login and Register, with the mark and the theme toggle |
| `PageLayout` | one article at a single width, with its title and lead line |
| `CardGrid` + `PageCard` | a grid of cards, one per note or page: a title and a text, and a footer with a date and a status label |
| `AdminRow` + `AdminAdd` | one admin row (rename, move up/down, delete) and the small form that adds a module, section or page |
