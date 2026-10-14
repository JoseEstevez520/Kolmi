-- A live session can mirror one of its author's notes: the note keeps being a normal note and
-- the session carries its text to the class. Also in schema.sql. Safe to run more than once.
alter table live_notes
  add column if not exists note_id bigint references notes(id) on delete set null;
