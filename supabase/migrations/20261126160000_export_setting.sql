alter table public.settings add column if not exists export_enabled boolean not null default true;
