# AGENTS.md

Kolmi is a collaboration app for a class. This repo is the product; the class material lives
in its own repo.

## What's here

- `backend/` — Python + FastAPI API.
- `frontend/` — Vue 3 + Vite web.
- `landing/` — the project's public page, static, built with the same library. Not part of a
  class's instance: see [landing/README.md](landing/README.md).
- `docs/` — the idea, specs and brand tone.

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
- **Agents use the OpenAI SDK.** Move to LangGraph only when loops or approval are needed.
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
