-- Account status has replaced the approval flag.
alter table public.profiles drop column if exists approved;

-- Shared by API workers and the scheduled pass.
alter table public.nodes add column if not exists rebuild_started_at timestamptz;
