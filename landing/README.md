# Landing

Kolmi's public page: what it is, how it works and how to run it, for whoever is thinking of
bringing it to their class. It is not part of a class's instance. `docker-compose.yml` never
builds it, and a class that deploys Kolmi doesn't need it.

## What it says

It follows the [README](../README.md) section by section. Where the README shows a screenshot,
the landing shows the real thing, built from the app's own parts:

| README | Landing |
|---|---|
| `before-after` | the two notes as cards with their status, and the page the pass wrote from them, with its diagram |
| How it works | an `AgentReplay` of that night's pass (made up and shortened, and it says so), then the table |
| What you can do today | the lists, and the admin's schedule controls (`WeekPillbox`, `DayStrip`) to try |
| `diagram`, `chart`, `page` | a `Diagram`, a `Chart` and a `CodeBlock` with its `Callout`, with the class pages' content |

The texts live in `src/locales/en.js` and `es.js`, taken from `README.md` and `README.es.md`.
When the README changes, the landing changes in the same commit, in both languages.

## How it looks

Everything in [frontend/design.md](../frontend/design.md) and
[docs/brand-visuals.md](../docs/brand-visuals.md) applies: elastic-ui's parts, the app's
tokens, grey by default, no shadows of our own, one width and one column.

One exception, on purpose: **the honey aurora is the landing's decoration**. The app keeps it
for AI at work. The landing uses it the way the class invitation does: it fills the first screen
and the closing one, and `AgentReplay` brings its own in between. Two rules still hold. Text on
it is `fg` or `fg-secondary` only, with no card or fill of our own over it. And there is always
a grey section between two auroras.

The tokens at the top of `src/style.css` are a copy of `frontend/src/style.css`'s. Keep them in
step. The library's Spanish labels are not copied: they are read from the app's
`frontend/src/locales/elastic-ui.es.js`.

## Run it

```bash
cd landing
npm install
npm run dev      # on :5173
npm run build    # a static site in dist/
```

It installs elastic-ui from the app's packed copy, `../frontend/vendor/`. When the app bumps the
library, bump `package.json` here too.

## Deploy it

`npm run build` gives a static folder, `dist/`, that any web server can serve. Where yours runs
(the server, the domain, the certificate) is personal setup and goes in `LOCAL.md`, never here.
