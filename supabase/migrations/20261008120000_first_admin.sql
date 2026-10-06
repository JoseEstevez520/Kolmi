-- The first admin: whoever signs up first on an instance with no admin becomes one, let in at once,
-- in place of ADMIN_EMAILS. Signing up already needs the class code, which keeps strangers out.
-- Accounts that already exist keep their role. Also in schema.sql. Safe to run more than once.
--
-- One function decides and inserts in the same transaction, under a lock that takes one sign-up
-- at a time: two at once on an instance with no admin can't both see none and both become one.
-- Anyone else is a student, waiting as pending while the class asks for approval.
create or replace function sign_up_profile(p_id uuid, p_name text)
returns profiles
language plpgsql
security definer
set search_path = public
as $$
declare
  created profiles;
begin
  perform pg_advisory_xact_lock(hashtext('kolmi.sign_up_profile'));
  if not exists (select 1 from profiles where role = 'admin') then
    insert into profiles (id, name, role, status)
    values (p_id, p_name, 'admin', 'active')
    returning * into created;
  else
    insert into profiles (id, name, role, status)
    values (
      p_id,
      p_name,
      'student',
      case
        when coalesce((select signups_need_approval from settings where id = 1), false) then 'pending'
        else 'active'
      end
    )
    returning * into created;
  end if;
  return created;
end;
$$;

-- Only the backend calls it, with the service role.
revoke all on function sign_up_profile(uuid, text) from public, anon, authenticated;
