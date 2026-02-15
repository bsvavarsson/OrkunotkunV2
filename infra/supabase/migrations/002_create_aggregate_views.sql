begin;

create or replace view energy.electricity_daily as
select
  date_trunc('day', measured_at at time zone 'Atlantic/Reykjavik')::date as day,
  sum(coalesce(delta_kwh, 0))::numeric(14, 4) as brutto_kwh
from energy.electricity_raw
group by 1;

create or replace view energy.ev_daily as
select
  date_trunc('day', coalesce(started_at, finished_at) at time zone 'Atlantic/Reykjavik')::date as day,
  sum(coalesce(energy_kwh, 0))::numeric(14, 4) as ev_kwh
from energy.ev_charger_raw
group by 1;

create or replace view energy.hot_water_daily as
select
  date_trunc('day', measured_at at time zone 'Atlantic/Reykjavik')::date as day,
  sum(coalesce(usage_value, 0))::numeric(14, 5) as hot_water_usage
from energy.hot_water_raw
group by 1;

create or replace view energy.weather_daily as
select
  date_trunc('day', measured_at at time zone 'Atlantic/Reykjavik')::date as day,
  avg(temperature_c)::numeric(8, 3) as avg_temperature_c,
  avg(humidity_percent)::numeric(8, 3) as avg_humidity_percent,
  avg(wind_speed_kmh)::numeric(8, 3) as avg_wind_speed_kmh
from energy.weather_raw
group by 1;

create or replace view energy.dashboard_daily as
select
  electricity.day,
  electricity.brutto_kwh,
  coalesce(ev.ev_kwh, 0)::numeric(14, 4) as ev_kwh,
  (electricity.brutto_kwh - coalesce(ev.ev_kwh, 0))::numeric(14, 4) as netto_kwh,
  coalesce(hot.hot_water_usage, 0)::numeric(14, 5) as hot_water_usage,
  weather.avg_temperature_c
from energy.electricity_daily electricity
left join energy.ev_daily ev on ev.day = electricity.day
left join energy.hot_water_daily hot on hot.day = electricity.day
left join energy.weather_daily weather on weather.day = electricity.day;

commit;
