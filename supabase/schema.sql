-- Kolmi schema. Paste this into the Supabase SQL editor.
-- Run it once per instance (one instance per class).

create table if not exists profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  name text not null,
  role text not null default 'student' check (role in ('student', 'admin')),
  approved boolean not null default true,
  created_at timestamptz not null default now()
);

-- Content: module → sections → pages.
create table if not exists modules (
  id bigserial primary key,
  name text not null,
  position int not null default 0,
  created_at timestamptz not null default now()
);

create table if not exists sections (
  id bigserial primary key,
  module_id bigint not null references modules(id) on delete cascade,
  name text not null,
  position int not null default 0,
  created_at timestamptz not null default now()
);

create table if not exists pages (
  id bigserial primary key,
  section_id bigint not null references sections(id) on delete cascade,
  title text not null,
  content_md text not null default '',   -- the canonical, chunked for the RAG
  content_web text not null default '',  -- the OpenUI Lang the frontend paints
  position int not null default 0,
  updated_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

-- Previous versions of a page, saved on every AI change.
create table if not exists page_versions (
  id bigserial primary key,
  page_id bigint not null references pages(id) on delete cascade,
  content_md text not null default '',
  content_web text not null default '',
  created_at timestamptz not null default now()
);

create table if not exists notes (
  id bigserial primary key,
  user_id uuid not null references profiles(id) on delete cascade,
  content text not null,
  format text not null default 'text',   -- text | rich (future editor)
  module_id bigint references modules(id) on delete set null,
  page_id bigint references pages(id) on delete set null,
  status text not null default 'pending'
    check (status in ('pending', 'processed', 'discarded')),
  created_at timestamptz not null default now()
);

-- RLS on, with no public policies: only the backend (service role) gets in.
alter table profiles enable row level security;
alter table modules enable row level security;
alter table sections enable row level security;
alter table pages enable row level security;
alter table page_versions enable row level security;
alter table notes enable row level security;
