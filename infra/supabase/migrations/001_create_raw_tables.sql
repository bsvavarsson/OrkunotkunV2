begin;

create schema if not exists energy;

create table if not exists energy.ingestion_runs (
  id bigint generated always as identity primary key,
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  status text not null check (status in ('running', 'success', 'partial_success', 'failed')),
  source_count integer not null default 0,
  success_count integer not null default 0,
  failure_count integer not null default 0,
  details jsonb not null default '{}'::jsonb
);

create table if not exists energy.source_status (
  id bigint generated always as identity primary key,
  source_name text not null,
  checked_at timestamptz not null default now(),
  status text not null check (status in ('success', 'failed', 'partial', 'empty')),
  failure_category text,
  message text,
  run_id bigint references energy.ingestion_runs(id) on delete set null,
  details jsonb not null default '{}'::jsonb
);

create index if not exists idx_source_status_source_checked_at
  on energy.source_status (source_name, checked_at desc);

create table if not exists energy.electricity_raw (
  id bigint generated always as identity primary key,
  source text not null default 'hsveitur',
  meter_id text,
  delivery_point_name text,
  measured_at timestamptz not null,
  delta_kwh numeric(12, 4),
  index_value numeric(14, 4),
  ambient_temperature_c numeric(8, 3),
  unit_code text,
  utility_type text,
  source_payload jsonb not null,
  ingestion_run_id bigint references energy.ingestion_runs(id) on delete set null,
  created_at timestamptz not null default now(),
  unique (source, meter_id, measured_at)
);

create index if not exists idx_electricity_raw_measured_at
  on energy.electricity_raw (measured_at desc);

create table if not exists energy.ev_charger_raw (
  id bigint generated always as identity primary key,
  source text not null default 'zaptec',
  charger_id text,
  charger_name text,
  session_id text,
  started_at timestamptz,
  finished_at timestamptz,
  energy_kwh numeric(12, 4),
  duration_seconds integer,
  source_payload jsonb not null,
  ingestion_run_id bigint references energy.ingestion_runs(id) on delete set null,
  created_at timestamptz not null default now(),
  unique (source, charger_id, session_id)
);

create index if not exists idx_ev_charger_raw_started_at
  on energy.ev_charger_raw (started_at desc);

create table if not exists energy.hot_water_raw (
  id bigint generated always as identity primary key,
  source text not null default 'veitur',
  permanent_number text,
  measured_at timestamptz not null,
  usage_value numeric(14, 5),
  usage_unit text,
  data_status integer,
  source_payload jsonb not null,
  ingestion_run_id bigint references energy.ingestion_runs(id) on delete set null,
  created_at timestamptz not null default now(),
  unique (source, permanent_number, measured_at)
);

create index if not exists idx_hot_water_raw_measured_at
  on energy.hot_water_raw (measured_at desc);

create table if not exists energy.weather_raw (
  id bigint generated always as identity primary key,
  source text not null default 'open_meteo',
  measured_at timestamptz not null,
  temperature_c numeric(8, 3),
  humidity_percent numeric(8, 3),
  wind_speed_kmh numeric(8, 3),
  source_payload jsonb not null,
  ingestion_run_id bigint references energy.ingestion_runs(id) on delete set null,
  created_at timestamptz not null default now(),
  unique (source, measured_at)
);

create index if not exists idx_weather_raw_measured_at
  on energy.weather_raw (measured_at desc);

commit;
