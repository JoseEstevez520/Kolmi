# AGENTS.md

Kolmi is a collaboration app for a class. This repo is the product; the class material lives
in its own repo.

## What's here

- `backend/` — Python + FastAPI API.
- `frontend/` — Vue 3 + Vite web.
- `docs/` — the idea, specs and brand tone.

## Rules

- **One instance per class.** No multitenancy: each class deploys its own, with its own
  Supabase and server.
- **No secrets in git.** Supabase keys and `CLASS_CODE` go in `.env`, never in the repo.
- **Agents use the OpenAI SDK.** Move to LangGraph only when loops or approval are needed.
- **Everything in this repo is in English** (code, comments, docs, commits).
- **Personal setup is local.** This developer's own server, Supabase and deploy details live
  in `LOCAL.md` (gitignored). If it exists, read it for the instance-specific context.
