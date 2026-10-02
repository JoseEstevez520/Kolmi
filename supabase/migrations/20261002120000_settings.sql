-- The class settings: one row per instance (one instance per class).
-- class_language is the language the AI writes the shared notes and pages in.
-- Safe to run more than once.

create table if not exists settings (
  id smallint primary key default 1 check (id = 1),
  class_language text not null default 'en',
  updated_at timestamptz not null default now()
);

-- No seed row: until the admin first saves, the backend uses CLASS_LANGUAGE.

-- Whether the caller is an admin. Security definer so it can read profiles, which has RLS
-- on and no policies of its own.
create or replace function public.is_admin()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1 from public.profiles where id = auth.uid() and role = 'admin'
  );
$$;

alter table settings enable row level security;

-- The backend uses the service role and skips RLS. These cover a direct client:
-- everyone signed in reads, only admins write.
drop policy if exists "settings_read" on settings;
create policy "settings_read" on settings
  for select to authenticated using (true);

drop policy if exists "settings_admin_insert" on settings;
create policy "settings_admin_insert" on settings
  for insert to authenticated with check (public.is_admin());

drop policy if exists "settings_admin_update" on settings;
create policy "settings_admin_update" on settings
  for update to authenticated using (public.is_admin()) with check (public.is_admin());
