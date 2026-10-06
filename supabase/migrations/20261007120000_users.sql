-- Users from the admin panel: a status apart from the role, approval for new sign-ups, and files
-- that outlive their author. Also in schema.sql. Safe to run more than once.

-- What a person may do, apart from their role: active, pending (waiting for an admin to let
-- them in) or blocked. It takes over from `approved`, which is no longer read but stays for now.
-- A profile not approved becomes pending, only when the column is first added: run again, it
-- leaves alone whoever an admin has let in since.
do $$
begin
  if not exists (
    select 1 from information_schema.columns
    where table_schema = 'public' and table_name = 'profiles' and column_name = 'status'
  ) then
    alter table profiles add column status text not null default 'active'
      check (status in ('active', 'pending', 'blocked'));
    update profiles set status = 'pending' where approved = false;
  end if;
end $$;

-- For when the class code leaks: new sign-ups wait for an admin.
alter table settings add column if not exists signups_need_approval boolean not null default false;

-- A file on a shared page stays when its author's account goes; it is left with no author.
-- A note's files still go with the note (files.note_id cascades).
alter table files alter column user_id drop not null;
alter table files drop constraint if exists files_user_id_fkey;
alter table files add constraint files_user_id_fkey
  foreign key (user_id) references profiles(id) on delete set null;
