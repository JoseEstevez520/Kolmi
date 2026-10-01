-- Kolmi schema. Paste this into the Supabase SQL editor.
-- Run it once per instance (one instance per class).

create table if not exists profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  name text not null,
  role text not null default 'student' check (role in ('student', 'admin')),
  approved boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists notes (
  id bigserial primary key,
  user_id uuid not null references profiles(id) on delete cascade,
  content text not null,
  format text not null default 'text',   -- text | rich (future editor)
  module_id bigint,                       -- set in a later phase
  page_id bigint,                         -- set in a later phase
  status text not null default 'pending'
    check (status in ('pending', 'processed', 'discarded')),
  created_at timestamptz not null default now()
);

-- RLS on, with no public policies: only the backend (service role) gets in.
alter table profiles enable row level security;
alter table notes enable row level security;
