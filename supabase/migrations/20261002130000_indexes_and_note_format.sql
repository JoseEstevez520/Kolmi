-- Indexes for what the backend filters and joins on, and the note formats the API accepts.
-- Safe to run more than once.

create index if not exists notes_status_idx on notes (status);
create index if not exists notes_user_id_idx on notes (user_id);
create index if not exists notes_node_id_idx on notes (node_id);
create index if not exists nodes_parent_position_idx on nodes (parent_id, position);
create index if not exists node_versions_node_id_idx on node_versions (node_id);
create index if not exists ai_log_pass_id_idx on ai_log (pass_id);
create index if not exists ai_log_note_id_idx on ai_log (note_id);
create index if not exists ai_log_created_at_idx on ai_log (created_at desc);
create index if not exists ai_passes_started_at_idx on ai_passes (started_at desc);

alter table notes drop constraint if exists notes_format_check;
alter table notes add constraint notes_format_check check (format in ('text', 'markdown'));
