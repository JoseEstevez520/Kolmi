# Backend

Python + FastAPI API. No code yet.

## What it will do

- Validate the Supabase token on every request.
- Accounts: `GET /profile`, `POST /register`, `POST /notes`, `GET /notes/mine`.
- The daily agent job.

The account details are in [`../docs/authentication.md`](../docs/authentication.md).

## Environment variables

`SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `CLASS_CODE`. In `.env`, never in git.
