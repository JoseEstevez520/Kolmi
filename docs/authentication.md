# Authentication and users

Accounts, login and sign-up for the Kolmi app. This is only that part: the agent job, the
notes pages and the chat/RAG are out of scope.

## Context

The app is for a single class, not several (no multitenancy). Students leave notes and a
daily job turns them into notes. Here we only cover accounts.

Stack:

- **Supabase** (cloud, free plan): Auth and Postgres.
- **Own backend** on a server, with Python and FastAPI.
- **Frontend**: the existing web, adapted.

## Login

Two methods at once:

1. **Google**, with the Supabase Auth provider.
2. **Email and password**, with Supabase's native Auth.

Passwords are stored by Supabase Auth (hashed); neither the backend nor the admin ever sees
them. The email form calls `supabase.auth.signUp` / `signInWithPassword` directly from the
frontend. To recover a password, `resetPasswordForEmail`.

In Supabase, Authentication → Providers → Email, turn "Confirm email" off on sign-up, or set
up your own SMTP (Resend, Brevo) if you want it on.

## Class code and profile

After the **first** login (with any method), if the user has no profile, they're asked for a
**class code** and a **display name** (prefilled with the Google one if it exists). The code
is in a backend environment variable, `CLASS_CODE`. Without a profile, no notes can be left.

## Database

Two tables in Supabase:

```sql
create table profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  name text not null,
  role text default 'student',  -- student | admin
  approved boolean default true,
  created_at timestamptz default now()
);

create table notes (
  id bigserial primary key,
  user_id uuid references profiles(id) on delete cascade,
  content text not null,
  format text default 'text',  -- text | rich (future)
  status text default 'pending',  -- pending | processed | discarded
  created_at timestamptz default now()
);
```

Both with RLS (Row Level Security: each row decides who can read or write it) on and **no
public policies**: only the backend gets in, with the service role key.

## Backend (FastAPI)

Every route receives `Authorization: Bearer <Supabase access token>` and validates it with
`supabase.auth.get_user(token)`.

| Route | What it does |
|---|---|
| `GET /profile` | the user's profile, or 404 if it doesn't exist |
| `POST /register` | `{code, name}`: validates the code against `CLASS_CODE` and creates the profile. 403 if the code is wrong |
| `POST /notes` | `{content}`: requires a profile with `approved = true` and saves the note as `pending` |
| `GET /notes/mine` | the user's own notes |

Environment variables: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `CLASS_CODE`. The service key
never leaves the backend.

## Frontend

- Login screen: a "Sign in with Google" button, an email and password form, and links to
  "Sign up" and "Forgot my password".
- `@supabase/supabase-js` with the anon key (public), only for login.
- After signing in, call `GET /profile`; if it returns 404, show the code and name screen.
- Main screen: a form to leave a note and a list of "my notes".

## Manual setup

1. Google Cloud Console: create OAuth credentials (Web) with the redirect URI Supabase
   shows.
2. Supabase → Authentication → Providers → Google: paste the client ID and secret.
3. Supabase → Authentication → URL Configuration: add the web domain.

These steps also go in the project README once it's set up.

## Out of scope

The daily agent job, the notes pages and the chat/RAG.
