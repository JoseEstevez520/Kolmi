-- Kolmi schema. Paste this into the Supabase SQL editor.
-- Run it once per instance (one instance per class).
-- Kept in sync with supabase/migrations/, which hold each change for an existing instance.

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
  format text not null default 'text'
    check (format in ('text', 'markdown')),  -- markdown comes from the notes editor
  node_id bigint references nodes(id) on delete set null,
  status text not null default 'pending'
    check (status in ('pending', 'processed', 'discarded')),
  created_at timestamptz not null default now()
);

-- Files on a page or on a note. Also in migrations/20261003130000_files.sql.
create table if not exists files (
  id bigserial primary key,
  node_id bigint references nodes(id) on delete cascade,
  note_id bigint references notes(id) on delete cascade,
  name text not null,
  size bigint not null,
  mime text not null default 'application/octet-stream',
  path text not null,  -- the object's key in the `files` bucket
  user_id uuid not null references profiles(id) on delete cascade,
  created_at timestamptz not null default now(),
  -- A file belongs to a page or to a note, never both: the pass moves it from one to the other.
  constraint files_belongs_check check (num_nonnulls(node_id, note_id) = 1)
);

create index if not exists files_node_id_idx on files (node_id);
create index if not exists files_note_id_idx on files (note_id);

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

-- What the backend filters and joins on. Also in
-- migrations/20261002130000_indexes_and_note_format.sql.
create index if not exists notes_status_idx on notes (status);
create index if not exists notes_user_id_idx on notes (user_id);
create index if not exists notes_node_id_idx on notes (node_id);
create index if not exists nodes_parent_position_idx on nodes (parent_id, position);
create index if not exists node_versions_node_id_idx on node_versions (node_id);
create index if not exists ai_log_pass_id_idx on ai_log (pass_id);
create index if not exists ai_log_note_id_idx on ai_log (note_id);
create index if not exists ai_log_created_at_idx on ai_log (created_at desc);
create index if not exists ai_passes_started_at_idx on ai_passes (started_at desc);

-- The class settings: one row per instance. class_language is the language the AI writes
-- the shared notes and pages in. Also in migrations/20261002120000_settings.sql.
create table if not exists settings (
  id smallint primary key default 1 check (id = 1),
  class_language text not null default 'en',
  updated_at timestamptz not null default now()
);

-- When the daily pass runs: on or off, the times (HH:MM, Europe/Madrid) and the ISO weekdays
-- (1 Monday to 7 Sunday). Also in migrations/20261003120000_pass_schedule.sql.
alter table settings add column if not exists pass_enabled boolean not null default true;
alter table settings add column if not exists pass_times text[] not null default '{03:00}';
alter table settings add column if not exists pass_days smallint[] not null default '{1,2,3,4,5,6,7}';

-- No seed row: until the admin first saves, the backend uses CLASS_LANGUAGE.

-- Whether the caller is an admin. Security definer so it can read profiles, which has RLS
-- on and no policies of its own.
create or replace function public.is_admin()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1 from public.profiles where id = auth.uid() and role = 'admin'
  );
$$;

-- RLS on, with no public policies: only the backend (service role) gets in.
alter table profiles enable row level security;
alter table nodes enable row level security;
alter table node_versions enable row level security;
alter table notes enable row level security;
alter table ai_passes enable row level security;
alter table ai_log enable row level security;
alter table settings enable row level security;
alter table files enable row level security;

-- settings is the one exception: everyone signed in reads it, only admins write it. The
-- backend still goes through the service role.
drop policy if exists "settings_read" on settings;
create policy "settings_read" on settings
  for select to authenticated using (true);

drop policy if exists "settings_admin_insert" on settings;
create policy "settings_admin_insert" on settings
  for insert to authenticated with check (public.is_admin());

drop policy if exists "settings_admin_update" on settings;
create policy "settings_admin_update" on settings
  for update to authenticated using (public.is_admin()) with check (public.is_admin());

-- Private bucket: the backend uploads, and hands out short-lived signed links to download.
insert into storage.buckets (id, name, public) values ('files', 'files', false)
on conflict (id) do nothing;
