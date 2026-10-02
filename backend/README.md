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
into the Supabase SQL editor.

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
`LLM_BASE_URL`, `LLM_MODEL`) and, optionally, `CORS_ORIGINS`. In `.env`, never
in git.

## The daily pass

Once a day, a cron wakes a team of agents that turns the pending notes into
pages:

1. **Gatekeeper** — anonymizes, joins notes about the same topic, discards what
   adds nothing and decides the target page (an existing one or a new one).
2. **Notes** — writes the page's Markdown in the house style.
3. **Web** — turns it into the page fields. For now the source is Markdown and
   `content_web` (OpenUI Lang) stays empty; that lands with the page format.

Every change saves the previous version in `node_versions` first, and every
step leaves an entry in `ai_log`. One run is one row in `ai_passes`.

Run it by hand:

```bash
python -m app.passes.daily            # run it
python -m app.passes.daily --dry-run  # only ask the gatekeeper, write nothing
```

Or from the admin API with `run_pass()` (runs synchronously).

Cron, on the server:

```cron
0 4 * * * cd /srv/kolmi/backend && .venv/bin/python -m app.passes.daily >> /var/log/kolmi-pass.log 2>&1
```

The pass refuses to start while another one is still running (within the last
two hours).

## Routes

| Action | Route | Who |
|---|---|---|
| `get_profile` | `GET /profile` | any signed-in user |
| `register_profile` | `POST /register` | any signed-in user |
| `create_note` | `POST /notes` | approved profile |
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

Every route takes `Authorization: Bearer <Supabase access token>`.
