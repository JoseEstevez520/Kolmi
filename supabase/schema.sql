-- Kolmi schema. Paste this into the Supabase SQL editor.
-- Run it once per instance (one instance per class).
-- Kept in sync with the migrations applied through the Supabase MCP.

create table if not exists profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  name text not null,
  role text not null default 'student' check (role in ('student', 'admin')),
  approved boolean not null default true,
  created_at timestamptz not null default now()
);

-- Content: one tree of nodes. A section groups, a page holds the content.
create table if not exists nodes (
  id bigserial primary key,
  parent_id bigint references nodes(id) on delete cascade,
  kind text not null default 'page' check (kind in ('section', 'page')),
  title text not null,
  description text not null default '',
  icon text,
  color text,
  position int not null default 0,
  on_home boolean not null default false,
  content_md text not null default '',   -- Markdown, derived for the RAG
  content_web text not null default '',  -- OpenUI Lang the frontend paints
  updated_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

-- Previous versions of a page, saved on every AI change.
create table if not exists node_versions (
  id bigserial primary key,
  node_id bigint not null references nodes(id) on delete cascade,
  content_md text not null default '',
  content_web text not null default '',
  created_at timestamptz not null default now()
);

create table if not exists notes (
  id bigserial primary key,
  user_id uuid not null references profiles(id) on delete cascade,
  content text not null,
  format text not null default 'text',   -- text | markdown (the notes editor)
  node_id bigint references nodes(id) on delete set null,
  status text not null default 'pending'
    check (status in ('pending', 'processed', 'discarded')),
  created_at timestamptz not null default now()
);

-- One row per daily AI pass.
create table if not exists ai_passes (
  id bigserial primary key,
  status text not null default 'running'
    check (status in ('running', 'done', 'failed')),
  model text,
  stats jsonb not null default '{}'::jsonb,
  error text,
  started_at timestamptz not null default now(),
  finished_at timestamptz
);

-- What the AI did, one entry per note or page touched.
create table if not exists ai_log (
  id bigserial primary key,
  pass_id bigint references ai_passes(id) on delete cascade,
  note_id bigint references notes(id) on delete set null,
  node_id bigint references nodes(id) on delete set null,
  action text not null check (action in ('created', 'updated', 'discarded', 'flagged')),
  reason text not null default '',
  created_at timestamptz not null default now()
);

-- RLS on, with no public policies: only the backend (service role) gets in.
alter table profiles enable row level security;
alter table nodes enable row level security;
alter table node_versions enable row level security;
alter table notes enable row level security;
alter table ai_passes enable row level security;
alter table ai_log enable row level security;
