# Page format

How a page goes from the daily pass to the screen. The idea is in `features.md` ("Page
format"); this file covers the packages, the endpoints and how to change the catalogue.
Checked against the docs at openui.com and the npm registry in October 2026.

## The pieces

| Piece | What it is |
|---|---|
| `@openuidev/vue-lang` (0.3) | The Vue 3 runtime: `defineComponent`, `createLibrary`, `<Renderer>`, `createParser`. Peer deps are `vue >=3.5` and `zod` 3.25+ or 4. |
| `@openuidev/lang-core` (0.3) | The framework-agnostic core: parser, `generateSystemPrompt`, types. `vue-lang` depends on it. |
| `@openuidev/cli` (0.4) | `openui generate <entry>` writes a prompt and a library spec (`.spec.json`) from a file that exports a library. |
| OpenUI Gateway | One option for the web model (`WEB_PROMPT=gateway`). What used to be the Thesys C1 API. OpenAI-compatible, at `https://api.thesys.dev/v1/embed`, with a key from console.thesys.dev. It validates the OpenUI Lang against the library while it streams and repairs what it can. |

Model ids on the Gateway are `{provider}/{model}`, as on OpenRouter (`openai/gpt-5`,
`google/gemini-3.7-flash`). `GET /v1/embed/models` only lists the old C1 models
(`c1/...`), so it isn't the full list; models.dev's OpenRouter page is. OUI-1, the model
`features.md` mentions, only shows up in the OpenUI benchmark as self-hosted. The Gateway
doesn't offer it.

On the Gateway, `google/gemini-3.7-flash` scores 98.9% structural validity at about $0.01 a
page in the OpenUI benchmark (DeepSeek V4 Flash scores 85.8%). Without a web model, the main
model (DeepSeek) writes the pages; its pages parse with no errors when it gets the whole
catalogue prompt.

## The catalogue

`frontend/src/lib/openui/catalog.js` holds the components the model may use: their Zod
props and descriptions, with no renderers. Argument order is the order of the keys.

| Component | Drawn with |
|---|---|
| `Page(blocks)` | `Prose`. Always the root. |
| `Heading(text, level?)` | a plain `h2`/`h3` with a slug id |
| `Text(markdown)` | elastic-ui `Markdown`, flowing in the page's Prose |
| `CodeBlock(code, language?, title?)` | `CodeBlock` |
| `Callout(type, text, title?)` | `Callout` |
| `Steps(items)`, `StepItem(title, text)` | `Steps static` + `StepsItem` |
| `Diagram(label, svg, caption?)` | `Diagram`, with the SVG as an `<img>` so it cannot run scripts |
| `Artifact(title, html, height?)` | the escape hatch: an `iframe` with `sandbox="allow-scripts"` and no same-origin access |

`library.js` maps each name onto elastic-ui. `prompt.js` builds the same catalogue with
stub renderers so the CLI can load it in Node, and `prompt-options.js` has the preamble,
rules and example.

## Regenerating the prompt

After changing the catalogue or the prompt options:

```bash
cd frontend
npm run page-prompt
```

This runs `openui generate` and writes three files to `backend/app/agents/openui/`. Commit
them with the change.

- `page.txt` is the full prompt, for a model called directly. DeepSeek gets this one.
- `page.spec.json` is the library spec.
- `page.gateway.txt` is `generateSystemPrompt({ cloud: true, library, promptOptions })`, the
  configuration block the Gateway builds the prompt from and validates against. The web agent
  sends this one when it goes through the Gateway.

## The backend

`backend/app/agents/web.py` writes each page with the first model that manages it:

1. The web model (`WEB_*`), when one is set. It gets the whole catalogue prompt
   (`page.txt`), or the config block with `WEB_PROMPT=gateway`.
2. The main model (`LLM_*`), with the whole catalogue prompt, when the web model fails or
   isn't set. Once the web model has failed in a pass (out of credit, say), the rest of that
   pass skips it; the next pass tries it again.
3. Markdown from the notes agent, when neither answer is a page.

The answer
is parsed by a small Python parser (`agents/openui/__init__.py`). If the root is a `Page`,
the source goes to `content_web` and a Markdown view of it to `content_md`: text kept,
code as fences, callouts as `> [!TYPE]`, diagrams and artifacts named in one line.

With Markdown only, `content_web` stays empty. Either way the pass goes on, and its stats
record which model wrote each page (`pages[].model`) and why a model was passed over
(`web_fallbacks`).

## The frontend

`NodeView.vue` checks `content_web` with the parser (`canRender`). If it parses into a
`Page`, `<Renderer>` draws it; otherwise the page shows `content_md`. The renderer is
permissive: it draws what it can and reports prop errors through `onError`, which only logs
them.

## Not done yet

- **The router** from `features.md`: one model for every page for now, always the catalogue.
- **Autofix** (`/v1/autofix`, $0.02 per fix) for OpenUI Lang written by a model outside
  the Gateway. Not used yet: a page that doesn't parse falls back instead.
- **Telemetry**: `lang-core` sends install telemetry unless `OPENUI_TELEMETRY_DISABLED=1`
  or `DO_NOT_TRACK=1` is set. `npm run page-prompt` sets it for the CLI.
