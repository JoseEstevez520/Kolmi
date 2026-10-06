# Backend

Python + FastAPI API. The account side and the content tree (phase 1) are
built, plus the daily pass that turns notes into pages.

## How it works

Every feature is an **action**: a name, a description, a Pydantic params model,
a permission check and a handler. The registry (`app/actions/`) is the single
source: every caller runs one through `invoke` (role, then params), `app/api.py`
turns each action into an API route, and `app/actions/tools.py` offers the same
actions as tools to a model. See [docs/tools.md](../docs/tools.md).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt   # includes requirements.txt
cp .env.example .env                  # fill it in
```

Create the tables by pasting [`../supabase/schema.sql`](../supabase/schema.sql)
into the Supabase SQL editor. An instance created before a change to the schema
gets it from the matching file in [`../supabase/migrations/`](../supabase/migrations/),
pasted the same way (each one is safe to run twice).
Or run them with `psql "$SUPABASE_DB_URL" -f <file>`, where `SUPABASE_DB_URL` is the
session pooler URI from the project's Connect dialog (the direct host is IPv6-only).

## Files

Files live in a private Storage bucket (`files`) and a `files` table, both created by
[`../supabase/migrations/20261003130000_files.sql`](../supabase/migrations/20261003130000_files.sql).
Uploads go through the API (`POST /files/upload`, the file as the request body) and downloads
are short-lived signed links (`GET /files/download`). The limits and allowed kinds are in
`app/files.py`; until the migration is applied, the routes answer 503 and pages read as
without files.

A note needs some text or a file. A note is created empty only for its first file
(`for_files`), and cleared only while it has files; the daily pass skips a note with neither,
and a note of only files has its files judged without writing the page.

## Run

```bash
uvicorn app.main:app --reload
```

- Health: `GET /health`
- API docs: `http://localhost:8000/docs`

## Tests

```bash
SUPABASE_URL=http://localhost SUPABASE_SERVICE_KEY=test CLASS_CODE=test pytest -q
```

The settings need those three to load; any value does, as nothing is reached.

The daily pass is tested with a fake model and a fake store (`tests/fakes.py`),
so the suite spends no tokens and touches no network.

## Environment variables

`SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `CLASS_CODE`, the model (`LLM_API_KEY`,
`LLM_BASE_URL`, `LLM_MODEL`) and, optionally, a faster model for the chat only (`CHAT_MODEL`,
same endpoint and key), the web model (`WEB_*`), `CORS_ORIGINS` and
`CLASS_LANGUAGE`. In `.env`, never in git.

For search by meaning (see below), `EMBEDDING_API_KEY` and, optionally, `EMBEDDING_BASE_URL` (any
OpenAI-compatible endpoint, OpenAI by default) and `EMBEDDING_MODEL` (default
`text-embedding-3-small`, 1536 dimensions through `dimensions`, $0.02 per 1M tokens). DeepSeek, the
default chat provider, has no embeddings endpoint. A model must give 1536 dimensions or accept
`dimensions`.

A class gets its first admin by signing up first: on an instance with no admin, the first
sign-up becomes one (see `docs/authentication.md`). Roles change from the admin panel after that.

Two models, and what each is for:

- **The web model** (`WEB_*`, optional) composes the pages in OpenUI Lang, figures included.
  Pick one suited to it: the OpenUI Gateway's model, or DeepSeek flash.
- **The main model** (`LLM_*`) runs the daily pass, writes the pages when there is no web
  model or it fails, and draws a page's SVG figures and interactive pieces, which are only
  called when a page asks for one. It will also run the chat, so make it a capable one: on
  DeepSeek, `deepseek-v4-pro`.

How a page is written and drawn is in `../docs/page-format.md`.

`CLASS_LANGUAGE` (`en` or `es`, default `en`) is the language the daily pass
writes the shared notes and pages in. An admin can change it in the admin panel,
which stores it in the `settings` table; once that row exists it wins over the
variable. Without the table (before the migration in
`../supabase/migrations/` is applied) the variable decides. The supported codes
live in `app/class_settings.py`.

## The daily pass

On the schedule the admin sets, a cron wakes a team of agents that turns the pending notes into
pages:

1. **Gatekeeper**: anonymizes, decides whether each note adds something new to what the
   pages already say, joins notes about the same topic, discards what adds nothing and picks
   the target page (an existing one or a new one, and where the new one goes among its
   siblings: first, after a page, or last, with the reason in the AI log). It works like a coding agent: it gets the
   tree as an index (id, kind and title of each node) and each note with its hint, the node
   the student picked, if any. It reads the pages it needs with a `read_page` tool before
   deciding. If the model has no tools, or the loop fails, it decides from the index alone.
   `--dry-run` lists what it read under `read`.
2. **Notes**: writes or updates the page's Markdown (`content_md`), following the class notes
   site's writing guide. This Markdown is the page's source.
3. **Web**: turns that Markdown into the page in OpenUI Lang (`content_web`), and the main
   model draws any SVG figure or interactive piece it asks for, with the Markdown at hand. If
   no model manages it, the page keeps its previous web, or shows its Markdown when it had none.

Every change saves the previous version in `node_versions` first, and every
step leaves an entry in `ai_log`. One run is one row in `ai_passes`.

Run it by hand:

```bash
python -m app.passes.daily            # run it
python -m app.passes.daily --dry-run  # only ask the gatekeeper, write nothing
python -m app.passes.daily --if-due   # run only when the admin's schedule says so
```

Or from the admin API with `run_pass()`: it starts the pass in the background and answers
`started` or `already_running` at once; the pass shows up in the AI log.

The schedule (on or off, times in Europe/Madrid, weekdays) lives in `settings` and is set in
the admin. The cron runs every hour with `--if-due`, which runs the pass only when a chosen
time has passed since the last pass started, and otherwise exits 0 saying why. Plain
`python -m app.passes.daily` always runs. Cron, on the server (see [Deploy](#deploy-docker)
for the container version):

```cron
0 * * * * cd /srv/kolmi/backend && .venv/bin/python -m app.passes.daily --if-due >> /var/log/kolmi-pass.log 2>&1
```

The pass refuses to start while another one is still running (within the last
two hours).

If the gatekeeper's answer skips a pending note, the note stays pending and gets
a `flagged` row in `ai_log`, so the next pass tries it again. The third pass that
skips it marks it `discarded` and logs why (`MAX_SKIPPED_PASSES` in
`app/passes/daily.py`). `--dry-run` lists those notes under `would_give_up` and
changes nothing.

## Search by meaning

Pages are chunked at their headings and embedded into `page_chunks` (pgvector, created by
[`../supabase/migrations/20261010130000_page_chunks.sql`](../supabase/migrations/20261010130000_page_chunks.sql);
apply it before deploying). The daily pass and the page writes keep it current; the chat and
`search_pages` use a hybrid search (full text and vectors) over it. Without `EMBEDDING_API_KEY` the
index stays empty and both work as before, with the tree and plain word matching.

Index every page once, after setting the key (`--force` ignores the stored hashes):

```bash
.venv/bin/python -m app.rag reindex
.venv/bin/python -m app.rag reindex --force
```

### Measuring retrieval

`evals/rag_questions.json` (not in git: it names this instance's pages, so each class makes its
own with `make_rag_questions`) holds questions, each with the page that answers it and a
kind: `exact` (uses a term from the page), `paraphrase` (same idea, other words) or `concept`.
`evals/rag_retrieval.py` asks the app's own `search` each one, collapses the chunks to pages and
prints recall@1/3/8 and MRR, overall and per kind, plus the questions that missed. It only reads
the database; set the same environment as the server (including `EMBEDDING_API_KEY`).

```bash
.venv/bin/python -m evals.rag_retrieval
.venv/bin/python -m evals.rag_retrieval --only concept --verbose --json out.json
```

The ids in the questions point at one instance's pages. To write a set for yours, run
`.venv/bin/python -m evals.make_rag_questions --pages 28`: it has the configured model draft
questions from the page text and overwrites the file. Skim the result before trusting it.

## Routes

| Action | Route | Who |
|---|---|---|
| `get_profile` | `GET /profile` | any signed-in user, whatever their status |
| `register_profile` | `POST /register` | any signed-in user |
| `update_my_name` | `POST /profile/name` | any member |
| `delete_my_account` | `POST /profile/delete` | any signed-in user, whatever their status |
| `create_note` | `POST /notes` | any member |
| `update_note` | `POST /notes/update` | the note's author, until the daily pass |
| `my_notes` | `GET /notes/mine` | any signed-in user |
| `list_nodes` | `GET /nodes` | any signed-in user |
| `view_node` | `GET /node` | any signed-in user |
| `create_node` | `POST /node` | admin |
| `update_node` | `POST /node/update` | admin |
| `move_node` | `POST /node/move` | admin |
| `reorder_nodes` | `POST /node/reorder` | admin |
| `delete_node` | `POST /node/delete` | admin |
| `list_notes` | `GET /notes` | admin |
| `view_ai_log` | `GET /ai-log` | admin |
| `run_pass` | `POST /pass/run` | admin |
| `get_settings` | `GET /settings` | any signed-in user |
| `update_settings` | `POST /settings` | admin |
| `delete_note` | `POST /notes/delete` | the note's author, until the daily pass |
| `search_pages` | `GET /search` | any member |
| `create_my_token` | `POST /tokens` | any member, from the app |
| `list_my_tokens` | `GET /tokens` | any member, from the app |
| `revoke_my_token` | `POST /tokens/revoke` | any member, from the app |
| `list_users` | `GET /users` | admin |
| `set_role` | `POST /users/role` | admin |
| `set_status` | `POST /users/status` | admin |
| `delete_user` | `POST /users/delete` | admin |

Every route takes `Authorization: Bearer <Supabase access token>`, or a personal token
(`kolmi_...`), which reaches only what is offered over the MCP. `/mcp` is the MCP server, with a
personal token: see [docs/mcp.md](../docs/mcp.md). "Any member" is an active
one: someone pending or blocked only gets the routes that say "whatever their status".

## Deploy (Docker)

The images are built from `backend/` (the API and the pass) and `frontend/` (the static
site, served by nginx, which also reverse-proxies `/api/` to the API — see
`frontend/nginx.conf`). The compose file lives at the repo root. `backend/.env` holds the
API's secrets; the repo root's own `.env` holds the frontend's build-time `VITE_*` vars
(public ones: Supabase's URL and anon key). Keep both out of git.

```bash
# Build the images
docker compose build

# Start the API and the frontend (each restarts on crash)
docker compose up -d api web

# Run the daily pass by hand
docker compose run --rm pass
docker compose run --rm pass python -m app.passes.daily --dry-run
```

The pass runs as a one-shot container, never as a cron inside the API. A host
cron wakes it every hour, and `--if-due` decides whether the admin's schedule asks for a pass:

```cron
0 * * * * cd /srv/kolmi && docker compose run --rm pass python -m app.passes.daily --if-due >> /var/log/kolmi-pass.log 2>&1
```

The API healthcheck hits `GET /health` every 30s.

### Going public

`web` is the only container with a published port, bound to `127.0.0.1` by default (see
`docker-compose.yml`): safe with no setup, reachable only from the host itself. `api` has
no host port at all; `web`'s nginx reaches it on the compose network (`http://api:8000`) and
proxies `/api/` to it, so the browser only ever talks to one origin — no CORS, no second
port to open, whatever fronts that one port. Pick whichever of these fits your server:

- **A domain and a reverse proxy** (Traefik, Dokploy, nginx, Caddy…) in front of `web`'s
  port, with its own TLS certificate (Let's Encrypt or similar). The usual way when the
  server already has a public IP and you're fine giving it a subdomain.
- **A tunnel**, when the server has no public IP or you'd rather not open a port: a
  Cloudflare Tunnel (needs a domain added to Cloudflare) or
  [Tailscale Funnel](https://tailscale.com/kb/1223/funnel) (no domain at all, a
  `https://<machine>.<tailnet>.ts.net` address; only serves ports 443, 8443 or 10000, so
  pick a free one and change `web`'s published port in `docker-compose.yml` to match).
- **Nothing**, for a class on one LAN or reached only over Tailscale/a VPN: `web`'s default
  `127.0.0.1` binding already covers that once you bind it to the right address instead
  (`0.0.0.0` for the LAN, or leave it as is behind Tailscale with `tailscale serve`).

Whichever you pick, set `CORS_ORIGINS` in `backend/.env` only if something ever calls the
API directly from a different origin than `web`'s; the app itself never needs it, since
`/api/` is same-origin.
