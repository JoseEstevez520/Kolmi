-- Bug reports carry a short, non-identifying environment line (browser, screen width, theme,
-- language) so the issue is useful to a developer. Also in schema.sql. Safe to run more than once.
alter table bug_reports add column if not exists environment text;
