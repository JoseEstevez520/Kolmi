-- Kolmi schema. Paste this into the Supabase SQL editor.
-- Run it once per instance (one instance per class).
-- Kept in sync with supabase/migrations/, which hold each change for an existing instance.

create table if not exists profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  name text not null,
  role text not null default 'student' check (role in ('student', 'admin')),
  approved boolean not null default true,  -- no longer read: status took over
  -- What they may do, apart from their role: active, pending (waiting for an admin) or blocked.
  -- Also in migrations/20261007120000_users.sql.
  status text not null default 'active' check (status in ('active', 'pending', 'blocked')),
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
  -- Where it was left from, and the page it came from if it was a link. Also in
  -- migrations/20261006120000_sources.sql.
  source text not null default 'web' check (source in ('web', 'chat', 'mcp')),
  source_url text,
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
  -- Who added it. A file on a shared page stays when its author's account goes, with no author;
  -- a note's files go with the note. Also in migrations/20261007120000_users.sql.
  user_id uuid references profiles(id) on delete set null,
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
  -- Who asked and through what; the daily pass has no user. Also in
  -- migrations/20261006120000_sources.sql.
  user_id uuid references profiles(id) on delete set null,
  source text not null default 'pass' check (source in ('pass', 'chat', 'mcp', 'web')),
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

-- The class's weekly timetable, for everyone to see (not the pass's own schedule above). On
-- or off, its days (ISO weekdays, 1 Monday to 7 Sunday, same shape as pass_days), when the
-- week starts and ends, and the breaks that run across every day. Also in
-- migrations/20261004100000_schedule.sql and 20261004110000_schedule_days_as_weekdays.sql.
alter table settings add column if not exists schedule_enabled boolean not null default false;
alter table settings add column if not exists schedule_days smallint[] not null default '{1,2,3,4,5}';
alter table settings add column if not exists schedule_start text not null default '08:10';
alter table settings add column if not exists schedule_end text not null default '15:20';
alter table settings add column if not exists schedule_breaks jsonb not null default '[]';
-- A real session's length in minutes, so dragging a slot in Admin always lands on a real
-- session (one, or two back to back), never an odd length.
alter table settings add column if not exists schedule_session_minutes smallint not null default 50;

-- The chat: off until an admin turns it on, with a daily message cap per student once it is.
-- Also in migrations/20261004140000_chat.sql.
alter table settings add column if not exists chat_enabled boolean not null default false;
alter table settings add column if not exists chat_daily_limit smallint not null default 20;

-- For when the class code leaks: new sign-ups wait for an admin. Also in
-- migrations/20261007120000_users.sql.
alter table settings add column if not exists signups_need_approval boolean not null default false;

-- How many notes a student may leave a day through their AI (the MCP); admins have no cap. Also in
-- migrations/20261009120000_api_tokens.sql.
alter table settings add column if not exists mcp_daily_notes smallint not null default 30;

-- Personal tokens, for the MCP: `kolmi_` and a random string, shown once; only its SHA-256 hash is
-- kept. Also in migrations/20261009120000_api_tokens.sql.
create table if not exists api_tokens (
  id bigserial primary key,
  user_id uuid not null references profiles(id) on delete cascade,
  name text not null,
  token_hash text not null unique,
  prefix text not null,
  last_used_at timestamptz,
  created_at timestamptz not null default now(),
  revoked_at timestamptz
);

create index if not exists api_tokens_user_id_idx on api_tokens (user_id);

-- One slot in the week: a class, a shift, a meeting. `node_id` links it to a page or section
-- (its title and colour are used when the slot has none of its own); null for a slot with no
-- page, such as a subject the class notes don't cover.
create table if not exists schedule_events (
  id bigint generated by default as identity primary key,
  node_id bigint references nodes(id) on delete set null,
  day smallint not null check (day >= 0 and day <= 6),
  start_time text not null,
  end_time text not null,
  title text,
  detail text,
  color text,
  created_at timestamptz not null default now()
);

-- One question asked and its answer, so the daily cap can be counted; a student's own history
-- too, though nothing reads it back yet.
create table if not exists chat_messages (
  id bigserial primary key,
  user_id uuid not null references profiles(id) on delete cascade,
  question text not null,
  answer text not null default '',
  sources bigint[] not null default '{}',
  created_at timestamptz not null default now()
);

create index if not exists chat_messages_user_id_created_at_idx
  on chat_messages (user_id, created_at);

-- A write the chat proposed and the person confirms or cancels. result is the tool's answer or
-- the error.
create table if not exists chat_proposals (
  id bigserial primary key,
  message_id bigint not null references chat_messages(id) on delete cascade,
  user_id uuid not null references profiles(id) on delete cascade,
  tool text not null,
  args jsonb not null default '{}',
  status text not null default 'pending' check (status in ('pending', 'running', 'done', 'cancelled')),
  result text,
  created_at timestamptz not null default now(),
  decided_at timestamptz
);

create index if not exists chat_proposals_message_id_idx on chat_proposals (message_id);

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
alter table schedule_events enable row level security;
alter table chat_messages enable row level security;
alter table chat_proposals enable row level security;
alter table api_tokens enable row level security;

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

-- Signing up: whoever signs up first on an instance with no admin becomes one, let in at once;
-- anyone else is a student, pending while the class asks for approval. One function decides and
-- inserts under a lock, so two sign-ups at once can't both become the first admin. Also in
-- migrations/20261008120000_first_admin.sql.
create or replace function sign_up_profile(p_id uuid, p_name text)
returns profiles
language plpgsql
security definer
set search_path = public
as $$
declare
  created profiles;
begin
  perform pg_advisory_xact_lock(hashtext('kolmi.sign_up_profile'));
  if not exists (select 1 from profiles where role = 'admin') then
    insert into profiles (id, name, role, status)
    values (p_id, p_name, 'admin', 'active')
    returning * into created;
  else
    insert into profiles (id, name, role, status)
    values (
      p_id,
      p_name,
      'student',
      case
        when coalesce((select signups_need_approval from settings where id = 1), false) then 'pending'
        else 'active'
      end
    )
    returning * into created;
  end if;
  return created;
end;
$$;

-- Only the backend calls it, with the service role.
revoke all on function sign_up_profile(uuid, text) from public, anon, authenticated;

-- Private bucket: the backend uploads, and hands out short-lived signed links to download.
insert into storage.buckets (id, name, public) values ('files', 'files', false)
on conflict (id) do nothing;
