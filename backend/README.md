# Backend

Python + FastAPI API. The account side (phase 1) is scaffolded; there's no
database beyond what `../supabase/schema.sql` creates yet.

## How it works

Every feature is an **action**: a name, a description, a Pydantic params model,
a permission check and a handler. The registry (`app/actions/`) is the single
source: `app/api.py` turns each action into an API route, and the same actions
will become the chat's tools (`Action.tool_schema()`).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill it in
```

Create the tables by pasting [`../supabase/schema.sql`](../supabase/schema.sql)
into the Supabase SQL editor.

## Run

```bash
uvicorn app.main:app --reload
```

- Health: `GET /health`
- API docs: `http://localhost:8000/docs`

## Environment variables

`SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `CLASS_CODE` and, optionally,
`CORS_ORIGINS`. In `.env`, never in git.

## Routes (phase 1)

| Action | Route | Who |
|---|---|---|
| `get_profile` | `GET /profile` | any signed-in user |
| `register_profile` | `POST /register` | any signed-in user |
| `create_note` | `POST /notes` | approved profile |
| `my_notes` | `GET /notes/mine` | any signed-in user |

Every route takes `Authorization: Bearer <Supabase access token>`.
