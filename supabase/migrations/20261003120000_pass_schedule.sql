-- When the daily pass runs, set by an admin: on or off, the times (HH:MM, Europe/Madrid) and
-- the ISO weekdays (1 Monday to 7 Sunday). Also in schema.sql.
alter table settings add column if not exists pass_enabled boolean not null default true;
alter table settings add column if not exists pass_times text[] not null default '{03:00}';
alter table settings add column if not exists pass_days smallint[] not null default '{1,2,3,4,5,6,7}';
