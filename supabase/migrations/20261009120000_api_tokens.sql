-- Personal tokens, for the MCP: a member's own AI acts as them, with their role and status. A
-- token is `kolmi_` and a random string, shown once when it is made; only its SHA-256 hash is
-- kept, with a short prefix to tell tokens apart in a list. Revoked, it stays for the record but
-- lets nothing in. Also in schema.sql. Safe to run more than once.
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

-- RLS on, with no public policies: only the backend (service role) gets in.
alter table api_tokens enable row level security;

-- How many notes a student may leave a day through their AI (the MCP): each costs a gatekeeper
-- call. Admins have no cap.
alter table settings add column if not exists mcp_daily_notes smallint not null default 30;
