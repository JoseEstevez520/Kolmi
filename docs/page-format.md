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
| `CodeDiff(before, after, file?)` | `CodeDiff`, a change to a file |
| `Callout(type, text, title?)` | `Callout` |
| `Steps(items)`, `StepItem(title, text)` | `Steps static` + `StepsItem` |
| `Table(columns, rows, caption?)` | a Markdown table, which `Markdown` draws as the library's |
| `DescriptionList(items)`, `DescriptionItem(term, text)` | `DescriptionList divided` |
| `Accordion(items)`, `AccordionItem(title, text)` | `Accordion type="multiple"`, for secondary detail only |
| `Cards(items)`, `Card(title, text?, href?, image?)` | a two-column grid of `Card`s; with `href` the whole card is a link, as the class site's reference cards |
| `Logos(names)` | technology names with their simple-icons logo (`logos.js`, a fixed set) |
| `TerminalReplay(entries, title?)`, `TerminalEntry(command, output?, comment?)` | `TerminalReplay` |
| `AgentReplay(events)`, `AgentPrompt`, `AgentStep`, `AgentAnswer` | `AgentReplay`; a step's icon is a name from the fixed set |
| `Chat(messages)`, `ChatMessage(role, text)` | `ChatMessage`s on a soft background |
| `Figure(label, parts, layout?, caption?)` | `Diagram` on `bg-bg-subtle`, its parts laid out in a row (a column on a phone), a column or a grid |
| `Group(parts, layout?)` | an untinted row, column or grid inside a Figure |
| `Area(title, parts, color?, icon?, note?, layout?)` | `diagram-area`: a tinted group with a title |
| `Chip(text, color?, icon?, note?)` | `diagram-chip`: a tinted part |
| `Label(text, icon?, color?)` | a plain line with an icon |
| `Arrow(label?, both?)` | a connector that points along its layout |
| `Diagram(label, brief, caption?, svg?)` | `Diagram`, with the SVG as an `<img>` so it cannot run scripts |
| `Artifact(title, brief, height?, html?)` | an `iframe` with `sandbox="allow-scripts"`, no same-origin access and a content policy with no network |

The figure pieces are elastic-ui's diagram classes (`diagram-area`, `diagram-chip`, tinted by
`--diagram-color`), so a model can compose the boxes-with-tints drawings the class notes site
draws by hand. Colours are names from a small palette (`colors.js`: blue, violet, cyan, pink,
yellow, grey, and green/amber/red for outcomes), and icons names from a fixed Lucide set
(`icon-names.js`). Both read in light and dark because the library mixes the tint with the
theme's own colours.

A Diagram's SVG and an Artifact's document get the elastic-ui tokens, resolved in the current
theme, and the diagram classes as plain CSS (`theme.js`), so they look like the app in both
themes; they are rebuilt when the theme changes.

### Diagrams and Artifacts

The page model does not write SVG or HTML. It writes a **brief** (what to show, its parts and
labels, the colour of each concept, what to notice) and leaves the last argument out. Once the
page parses, `draw_visuals` in `backend/app/agents/web.py` sends each brief to the main model
(`LLM_*`), checks the answer (an `<svg>` with a viewBox, no scripts, no event attributes, no
outside resources; or a whole HTML document) and writes it into the source. A bad answer is
sent back once with its problem; a failed call is tried once more. If the second answer fails
too, the block is taken out of the page, and the pass stats record it (`visuals`). The page
itself never fails because of a drawing. An SVG whose labels overlap (a rough measure of each
`<text>`'s box) is sent back once too, but kept if the second answer still overlaps. A block that already has its SVG or HTML (kept on an
update) is not drawn again.

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

The notes agent writes the page's Markdown first (`content_md`, the source). Then
`backend/app/agents/web.py` turns it into the page with the first model that manages it:

1. The web model (`WEB_*`), when one is set. It gets the whole catalogue prompt
   (`page.txt`), or the config block with `WEB_PROMPT=gateway`.
2. The main model (`LLM_*`), with the whole catalogue prompt, when the web model fails or
   isn't set. Once the web model has failed in a pass (out of credit, say), the rest of that
   pass skips it; the next pass tries it again.
3. Neither: `content_web` keeps what it had, so a failure never blanks a good page. A new page
   stays without one and shows its Markdown.

Then the main model draws the page's Diagram and Artifact briefs, if it has any, with the
page's Markdown as their data.

The web prompt's preamble is the class notes site's page guide (apuntes-web), in English; the
notes agent's prompt is its writing guide (apuntes-claros). Both live in this repo, ported by
hand.

**The setup we recommend**: a web model suited to OpenUI Lang for composing the pages and the
figures built from the library's pieces (the OpenUI Gateway's model, or DeepSeek flash), and
a capable main model, since it also writes the notes and draws the SVGs and Artifacts. On
DeepSeek, `LLM_MODEL=deepseek-v4-pro`.

The answer is parsed by a small Python parser (`agents/openui/__init__.py`). A `Page` root
with at least one block is a page. The pass stats record which model wrote each page
(`pages[].model`, `pages[].format`: `web`, `kept` or `markdown`) and why a model was passed
over (`web_fallbacks`).

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
