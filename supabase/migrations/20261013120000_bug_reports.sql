-- Bug reports: a student reports a problem with the app, an agent judges it and a genuine one
-- becomes a GitHub issue. Also in schema.sql. Safe to run more than once.
create table if not exists bug_reports (
  id bigserial primary key,
  user_id uuid references profiles(id) on delete set null,
  title text not null,
  body text not null,
  page_path text,
  -- pending: judged and waiting (or not judged yet); issue: filed; discarded: judged not genuine.
  status text not null default 'pending' check (status in ('pending', 'issue', 'discarded', 'failed')),
  -- {genuine, severity, title, body, reason}, or {error} when it failed
  verdict jsonb,
  issue_url text,
  created_at timestamptz not null default now()
);

create index if not exists bug_reports_user_id_idx on bug_reports (user_id, created_at desc);

-- How many reports a student may send a day; admins have no cap.
alter table settings add column if not exists bug_report_daily_limit smallint not null default 5;

-- RLS on, with no public policies: only the backend (service role) gets in.
alter table bug_reports enable row level security;
