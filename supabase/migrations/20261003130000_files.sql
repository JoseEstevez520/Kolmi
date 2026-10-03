-- Files: a page can carry files to download, and a note can carry files the daily pass may
-- move to a page. The bytes live in a private Storage bucket; this table says whose they are and
-- where. Safe to run more than once.

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

-- RLS on, with no public policies: only the backend (service role) gets in.
alter table files enable row level security;

-- Private bucket: the backend uploads, and hands out short-lived signed links to download.
insert into storage.buckets (id, name, public) values ('files', 'files', false)
on conflict (id) do nothing;
