# OrkunotkunV2

Local-first home energy analysis app.

## Current Scope (Phase A-C)

- Phase A: workspace structure and repository guardrails
- Phase B: endpoint connectivity harness for Veitur, HS Veitur, Zaptec, Open-Meteo
- Phase C: local Supabase schema/migration foundation

## Repository Structure

- `backend/` FastAPI backend + provider clients + tests
- `frontend/` React frontend (scaffold only in these phases)
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
   uv run pytest -m integration -q
   ```

4. Apply Supabase SQL migrations (local):

   Use your preferred local DB client against `127.0.0.1:54322` and run files in `infra/supabase/migrations` in order.

## Notes

- `.env` is ignored and must never be committed.
- Integration evidence is stored redacted under `docs/integration-evidence/`.
- See `PLAN-HANDOFF.md` for locked decisions and sequencing.