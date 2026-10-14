-- Live notes: one person writes during a class and the rest watch the text appear. Also in
-- schema.sql. Safe to run more than once.
create table if not exists live_notes (
  id bigserial primary key,
  -- Kept as a record if the author leaves the class.
  author_id uuid references profiles(id) on delete set null,
  title text not null,
  -- The timetable slot that was on when the session started, if any.
  event_id bigint references schedule_events(id) on delete set null,
  -- Plain text or Markdown, as written.
  content text not null default '',
  -- Off until the author shares it: until then only the author sees it.
  shared boolean not null default false,
  ended_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists live_notes_updated_at_idx on live_notes (updated_at desc);

-- RLS on, with no public policies: only the backend (service role) gets in.
alter table live_notes enable row level security;
