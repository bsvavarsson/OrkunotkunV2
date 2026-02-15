begin;

create or replace view public.dashboard_daily as
select *
from energy.dashboard_daily;

create or replace view public.source_status as
select
  id,
  source_name,
  checked_at,
  status,
  failure_category,
  message,
  run_id,
  details
from energy.source_status;

create or replace view public.ingestion_runs as
select
  id,
  started_at,
  finished_at,
  status,
  source_count,
  success_count,
  failure_count,
  details
from energy.ingestion_runs;

grant select on public.dashboard_daily to anon, authenticated;
grant select on public.source_status to anon, authenticated;
grant select on public.ingestion_runs to anon, authenticated;

commit;
