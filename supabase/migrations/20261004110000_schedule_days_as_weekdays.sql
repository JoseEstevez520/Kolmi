-- schedule_days was free text ("Monday", a name the admin typed); it becomes ISO weekdays
-- (1 Monday to 7 Sunday), the same shape as pass_days, so the admin picks real days with
-- WeekPillbox instead of typing names, and their display name comes from the locale. Also
-- in schema.sql.
alter table settings drop column if exists schedule_days;
alter table settings add column schedule_days smallint[] not null default '{1,2,3,4,5}';
