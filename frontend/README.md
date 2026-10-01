# Frontend

Vue 3 + Vite app for Kolmi, built on [elastic-ui](https://github.com/JoseEstevez520/elastic-ui).
Phase 1 covers accounts and notes: sign in, join with the class code, leave a note and see
your own notes.

## Setup

```bash
npm install
cp .env.example .env   # fill in the Supabase URL, anon key and API URL
npm run dev
```

Needs Node 20 or higher. The dev server runs on <http://localhost:5173>.

`.env` holds `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` (both public, from your Supabase
project) and `VITE_API_URL` (the backend, `http://localhost:8000` by default). It is
gitignored; only `.env.example` is committed.

## Build

```bash
npm run build
npm run preview
```

## How it fits together

- `src/lib/supabase.js` — the Supabase client, for login only.
- `src/lib/auth.js` — session and profile state, and the Supabase auth calls.
- `src/lib/api.js` — the backend client. Every request sends the session's access token as
  `Authorization: Bearer <token>`.
- `src/lib/content.js` — the shared module tree the sidebar lists; the admin panel refreshes it.
- `src/router/index.js` — after signing in, `GET /profile` decides the next screen: 404 goes
  to Register, otherwise Notes. `/admin` is kept for admins.
- `src/views/` — Login, Register, Notes, Section, Page and Admin.
- `src/components/` — the app shell (sidebar, page layout, cards) and the admin rows.

The design rules are in [`design.md`](design.md).
