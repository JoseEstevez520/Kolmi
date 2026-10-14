-- Profile photos: the object's key in the public `avatars` bucket (a random name, so the link
-- can't be guessed). Null means no photo and the app draws the initial. Safe to run more than once.

alter table profiles add column if not exists avatar_path text;

insert into storage.buckets (id, name, public) values ('avatars', 'avatars', true)
on conflict (id) do nothing;
