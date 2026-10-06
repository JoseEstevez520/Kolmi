# AGENTS.md

Kolmi is a collaboration app for a class. This repo is the product; the class material lives
in its own repo.

## What's here

- `backend/` — Python + FastAPI API.
- `frontend/` — Vue 3 + Vite web.
- `landing/` — the project's public page, static, built with the same library. Not part of a
  class's instance: see [landing/README.md](landing/README.md).
- `docs/` — the idea, specs and brand tone.

## Working here

- Backend tests, from `backend/` once its `.venv` is set up (see its README):
  `SUPABASE_URL=http://localhost SUPABASE_SERVICE_KEY=test CLASS_CODE=test .venv/bin/pytest -q`.
  They use fakes and touch no network.
- A change to the database is a new file in `supabase/migrations/`, mirrored in
  `supabase/schema.sql`, and the ROADMAP item says it has to be applied before deploying.
- Frontend: `npm run build` in `frontend/` and in `landing/`.

## Rules

- **One instance per class.** No multitenancy: each class deploys its own, with its own
  Supabase and server.
- **No secrets in git.** Supabase keys and `CLASS_CODE` go in `.env`, never in the repo.
- **UI pieces belong to elastic-ui.** [elastic-ui](https://github.com/JoseEstevez520/elastic-ui)
  is this project's own component library. Kolmi composes its parts; it doesn't build its own.
  If a screen or the page catalogue needs a piece the library lacks (a diagram part, a card, a
  frame), it is built in elastic-ui, following that repo's rules. Then it is released, and the
  packed version in `frontend/vendor/` is bumped. The same goes for a missing variant or a bug.
  See [frontend/design.md](frontend/design.md).
- **Look before you build.** Before writing a piece of code, check whether it already exists: in
  this repo, in a package already used, in the library's own docs, or as an established standard.
  When something exists, reuse it; when there are several ways, take the current standard over an
  older one, and say in the write-up what you looked at and why you chose it. Build it yourself
  only when nothing fits, and say so. This goes for dependencies, protocols (auth, tokens, MCP,
  streaming) and UI parts alike.
- **Agents use the OpenAI SDK, with their own loop.** Move one agent to LangGraph only when it
  must pause and resume its own reasoning, survive a long run or coordinate with other agents.
  Approval is not a reason: a turn ends with a proposal and the confirmation is a new request.
  Nor is state that lives in the database (a thread, a session).
- **Every feature is an action.** It is defined once in the registry (`backend/app/actions/`) and
  run through `invoke`, which checks the role and the params for the web, the chat and the MCP
  alike. A new action says whether it only reads and where a model may use it (`read_only`,
  `tool`, `mcp`), with a description and errors written for a model; `tests/test_tools.py` lists
  what each role is offered. See [docs/tools.md](docs/tools.md).
- **Give an agent real context, and trust its judgment over a mechanical gate.** A tight rule
  bolted on from outside (a category, a vote count, a keyword) is more likely to be wrong than a
  well-informed model: hand the agent what it needs to read (the tree, the pages it touches,
  related notes) and let it decide, the way the gatekeeper already reads a page before judging a
  note. The cost is real (more context, less predictable) and worth watching per pass, but it's
  not a reason to withhold the context or the judgment.
- **Everything in this repo is in English** (code, comments, docs, commits), except
  `README.es.md`, the Spanish translation of the README. The README always ships in both
  languages: edit one and the other in the same commit.
- **Personal setup is local.** This developer's own server, Supabase and deploy details live
  in `LOCAL.md` (gitignored). If it exists, read it for the instance-specific context.
- **Nothing personal in the repo.** The repo is the product, for any class. What belongs to one
  instance (its deploy, its tree, its notes, its own to-dos) never goes in the roadmap, the docs
  or the code: it goes in `LOCAL.md`.
