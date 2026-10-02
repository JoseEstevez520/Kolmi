# Backend

Python + FastAPI API. The account side and the content tree (phase 1) are
built, plus the daily pass that turns notes into pages.

## How it works

Every feature is an **action**: a name, a description, a Pydantic params model,
a permission check and a handler. The registry (`app/actions/`) is the single
source: `app/api.py` turns each action into an API route, and the same actions
will become the chat's tools (`Action.tool_schema()`).

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

## Run

```bash
uvicorn app.main:app --reload
```

- Health: `GET /health`
- API docs: `http://localhost:8000/docs`

## Tests

```bash
pytest
```

The daily pass is tested with a fake model and a fake store (`tests/fakes.py`),
so the suite spends no tokens and touches no network.

## Environment variables

`SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `CLASS_CODE`, the model (`LLM_API_KEY`,
`LLM_BASE_URL`, `LLM_MODEL`) and, optionally, the web model (`WEB_*`), `CORS_ORIGINS` and
`CLASS_LANGUAGE`. In `.env`, never in git.

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

Once a day, a cron wakes a team of agents that turns the pending notes into
pages:

1. **Gatekeeper** — anonymizes, joins notes about the same topic, discards what
   adds nothing and decides the target page (an existing one or a new one).
2. **Notes** — writes the page's Markdown in the house style.
3. **Web** — writes the page as OpenUI Lang (`content_web`) with its Markdown view
   (`content_md`), and the main model draws any SVG figure or interactive piece it asks for.
   If no model manages a page, the notes agent's Markdown is kept instead.

Every change saves the previous version in `node_versions` first, and every
step leaves an entry in `ai_log`. One run is one row in `ai_passes`.

Run it by hand:

```bash
python -m app.passes.daily            # run it
python -m app.passes.daily --dry-run  # only ask the gatekeeper, write nothing
```

Or from the admin API with `run_pass()` (runs synchronously).

Cron, on the server (see [Deploy](#deploy-docker) for the container version):

```cron
0 4 * * * cd /srv/kolmi/backend && .venv/bin/python -m app.passes.daily >> /var/log/kolmi-pass.log 2>&1
```

The pass refuses to start while another one is still running (within the last
two hours).

If the gatekeeper's answer skips a pending note, the note stays pending and gets
a `flagged` row in `ai_log`, so the next pass tries it again. The third pass that
skips it marks it `discarded` and logs why (`MAX_SKIPPED_PASSES` in
`app/passes/daily.py`). `--dry-run` lists those notes under `would_give_up` and
changes nothing.

## Routes

| Action | Route | Who |
|---|---|---|
| `get_profile` | `GET /profile` | any signed-in user |
| `register_profile` | `POST /register` | any signed-in user |
| `create_note` | `POST /notes` | approved profile |
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

Every route takes `Authorization: Bearer <Supabase access token>`.

## Deploy (Docker)

The image is built from this folder. The compose file lives at the repo root and
reads secrets from `backend/.env`, so keep that file on the server.

```bash
# Build the image
docker compose build

# Start the API (restarts on crash)
docker compose up -d api

# Run the daily pass by hand
docker compose run --rm pass
docker compose run --rm pass python -m app.passes.daily --dry-run
```

The pass runs as a one-shot container, never as a cron inside the API. A host
cron wakes it once a day:

```cron
0 4 * * * cd /srv/kolmi && docker compose run --rm pass python -m app.passes.daily >> /var/log/kolmi-pass.log 2>&1
```

The API healthcheck hits `GET /health` every 30s.
