# OrkunotkunV2

Local-first home energy analysis app.

## Current Scope (Phase A-D, partial)

- Phase A: workspace structure and repository guardrails
- Phase B: endpoint connectivity harness for Veitur, HS Veitur, Zaptec, Open-Meteo
- Phase C: local Supabase schema/migration foundation
- Phase D: ingestion runner writing source data into `energy` raw tables

## Repository Structure

- `backend/` FastAPI backend + provider clients + tests
- `frontend/` React frontend (scaffold only currently)
- `infra/supabase/` SQL migrations and schema assets
- `docs/` implementation docs and redacted integration evidence

## Local Prerequisites

- Python 3.11+
- `uv`
- Node.js 20+
- `pnpm`
- Docker with Supabase local stack running

## Quick Start

1. Copy env template and fill values:

   ```bash
   cp .env.example .env
   ```

2. Backend dependencies:

   ```bash
   cd backend
   uv sync
   ```

3. Run provider integration smoke tests:

   ```bash
   .venv/bin/pytest -m integration -q
   ```

4. Run ingestion backfill (example):

   ```bash
   .venv/bin/python -m app.ingest.run_backfill --from 2026-01-01 --to 2026-02-14
   ```

5. Apply Supabase SQL migrations (local):

   Use your preferred local DB client against `127.0.0.1:54322` and run files in `infra/supabase/migrations` in order.

## Notes

- `.env` is ignored and must never be committed.
- Integration evidence is stored redacted under `docs/integration-evidence/`.
- Weather is stored as hourly raw data in `energy.weather_raw`; daily averages come from `energy.weather_daily`.
- Veitur hot water is stored with interval semantics (`period_usage_value`, `interval_start_at`, `interval_end_at`, `interval_days`) and expanded to daily in `energy.hot_water_daily`.
- See `docs/PLAN-HANDOFF.md` for locked decisions and sequencing.