-- The chat: off until an admin turns it on, with a daily message cap per student once it is.
-- Also in schema.sql.
alter table settings add column if not exists chat_enabled boolean not null default false;
alter table settings add column if not exists chat_daily_limit smallint not null default 20;

-- One row per question asked, so the daily cap can be counted and the answer kept (for the
-- student to see their own history; nobody else's).
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

-- RLS on, with no public policies, as every table but settings: only the backend (service
-- role) gets in. It checks the daily cap and who asked itself.
alter table chat_messages enable row level security;
