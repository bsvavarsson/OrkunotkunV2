begin;

alter table energy.hot_water_raw
  add column if not exists period_usage_value numeric(14, 5),
  add column if not exists interval_start_at timestamptz,
  add column if not exists interval_end_at timestamptz,
  add column if not exists interval_days integer,
  add column if not exists daily_estimation numeric(14, 5),
  add column if not exists reading_value numeric(14, 5);

update energy.hot_water_raw
set
  period_usage_value = coalesce(period_usage_value, usage_value),
  interval_days = coalesce(interval_days, nullif((source_payload ->> 'readingDays')::integer, null), 0),
  interval_end_at = coalesce(interval_end_at, measured_at),
  interval_start_at = coalesce(
    interval_start_at,
    measured_at - make_interval(days => coalesce(nullif((source_payload ->> 'readingDays')::integer, null), interval_days, 0))
  ),
  daily_estimation = coalesce(daily_estimation, nullif((source_payload ->> 'dailyEstimation')::numeric, null)),
  reading_value = coalesce(reading_value, nullif((source_payload ->> 'readingValue')::numeric, null))
where true;

create or replace view energy.hot_water_daily as
with interval_rows as (
  select
    id,
    (interval_start_at at time zone 'Atlantic/Reykjavik')::date as start_day,
    (interval_end_at at time zone 'Atlantic/Reykjavik')::date as end_day,
    interval_days,
    coalesce(
      nullif(daily_estimation, 0),
      case
        when coalesce(interval_days, 0) > 0 then period_usage_value / interval_days
        else null
      end,
      0
    )::numeric(14, 5) as allocated_daily_usage
  from energy.hot_water_raw
  where coalesce(interval_days, 0) > 0
    and interval_end_at > interval_start_at
), expanded_intervals as (
  select
    day::date as day,
    allocated_daily_usage
  from interval_rows,
  lateral generate_series(start_day, end_day - 1, interval '1 day') as day
), zero_day_rows as (
  select
    date_trunc('day', coalesce(interval_end_at, measured_at) at time zone 'Atlantic/Reykjavik')::date as day,
    coalesce(period_usage_value, usage_value, 0)::numeric(14, 5) as allocated_daily_usage
  from energy.hot_water_raw
  where coalesce(interval_days, 0) = 0
)
select
  day,
  sum(allocated_daily_usage)::numeric(14, 5) as hot_water_usage
from (
  select day, allocated_daily_usage from expanded_intervals
  union all
  select day, allocated_daily_usage from zero_day_rows
) usage_by_day
group by day;

commit;
