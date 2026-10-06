-- Where a change came from, so the log can tell the daily pass, the chat, the MCP and the web
-- apart, and who asked. Also in schema.sql.
alter table notes add column if not exists source text not null default 'web'
  check (source in ('web', 'chat', 'mcp'));
alter table notes add column if not exists source_url text;

alter table ai_log add column if not exists user_id uuid references profiles(id) on delete set null;
alter table ai_log add column if not exists source text not null default 'pass'
  check (source in ('pass', 'chat', 'mcp', 'web'));
