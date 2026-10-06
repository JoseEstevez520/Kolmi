-- A write the chat proposed and the person confirms or cancels: a turn ends with the proposal,
-- the confirmation is a new request. Also in schema.sql. Safe to run more than once.
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

-- RLS on, with no public policies: only the backend (service role) gets in.
alter table chat_proposals enable row level security;
