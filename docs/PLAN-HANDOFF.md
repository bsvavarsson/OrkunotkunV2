# OrkunotkunV2 — Handoff Plan (Local-First MVP)

Last updated: 2026-02-14

## 0) Progress snapshot (as of 2026-02-14)

### Completed in this session
- ✅ Phase A completed (workspace structure + `.github` templates + guardrails).
- ✅ Phase B completed (provider clients + integration smoke harness + failure classification + test matrix doc).
- ✅ Phase C completed (Supabase migrations created and successfully applied to local Docker DB).

### Validation results
- Unit tests: `5 passed`.
- Integration tests: `2 passed`, `3 skipped`.
   - Veitur skipped due to no data in selected date range (`empty` classification captured).
   - HS Veitur skipped due to endpoint contract mismatch / `404` (`schema` classification captured).
   - Invalid-auth Zaptec test skipped unless `RUN_INVALID_AUTH_TESTS=1`.

### Database verification (local Supabase)
- Created `energy` schema with tables:
   - `electricity_raw`, `ev_charger_raw`, `hot_water_raw`, `weather_raw`, `ingestion_runs`, `source_status`
- Created views:
   - `electricity_daily`, `ev_daily`, `hot_water_daily`, `weather_daily`, `dashboard_daily`

### Next phase to execute
- Start at **Phase D — Ingestion and API**.

## 1) Goal and current state

### Goal
Build a local-first home energy analysis app, then prepare for deployment on Vercel + hosted Supabase.

### Current state in repository
- Present files:
  - `Orkunotkun.drawio` (screen + architecture concept)
  - `API-Endpoints.md` (provider endpoint notes)
  - `.env` (credentials and local configuration)
- Not yet created:
  - frontend/backend source code
  - Supabase schema/migrations
  - workspace scaffolding (`.github`, docs, tests, scripts)

## 2) Locked decisions (do not change unless user requests)

- Stack: React frontend + FastAPI backend + Supabase.
- Repo style: `pnpm` workspace for JS side.
- Python tooling: `uv` + `pyproject.toml`.
- Access model: invited users with email auth, shared household dashboard.
- Data refresh target: daily scheduled ingestion.
- Locale/timezone: `is-IS` and `Atlantic/Reykjavik`.
- KPI cards (v1): Brutto, Netto, EV Charger, Hot Water, Weather.
- Netto formula (v1): `Netto = Brutto - EV Charger`.
- Charts (v1):
  - Daily energy vs 3-month average
  - Daily hot-water trend (3 months)
  - EV charging trend
- Data-quality behavior: validate records, skip bad rows, log errors.
- UI scope: functional MVP (minimal, clean).
- Testing scope: broad unit + integration tests.

## 3) Hard requirements for implementation order

1. Endpoint connectivity tests must be implemented and executed first.
2. Only after endpoint tests are stable, scaffold full app architecture.
3. Local Supabase write path must work before frontend polishing.
4. Deployment-specific setup (Vercel + hosted Supabase) comes after local flow is proven.

## 4) Security and secret-handling constraints

- Never print secret values from `.env` in logs, commits, docs, or test output.
- Ensure `.env` is gitignored before any commit.
- Add `.env.example` with placeholders only.
- Keep provider credentials server-side only (never expose to frontend).

## 5) Executable task list (updated sequence)

### Phase A — Workspace structure and guardrails (completed)
1. Create top-level structure:
   - `frontend/`
   - `backend/`
   - `infra/supabase/`
   - `docs/`
   - `.github/ISSUE_TEMPLATE/`
2. Add baseline repo files:
   - `.gitignore`
   - `.env.example`
   - `README.md`
   - `.github/copilot-instructions.md`
   - `.github/pull_request_template.md`
   - `.github/ISSUE_TEMPLATE/bug_report.md`
   - `.github/ISSUE_TEMPLATE/feature_request.md`

### Phase B — Endpoint validation harness (completed)
3. Implement provider client layer in backend for:
   - Veitur (hot water)
   - HS Veitur (electricity)
   - Zaptec (EV, including OAuth token step)
   - Open-Meteo (weather)
4. Implement integration smoke tests that verify:
   - Auth works with current `.env`
   - Request/response mapping parses expected fields
   - Failure categories are classified (`auth`, `network`, `schema`, `empty`, `rate_limit`)
5. Store redacted test artifacts in `docs/integration-evidence/` (no secrets).

### Phase C — Supabase local foundation (completed)
6. Verify local Supabase Docker availability and ports.
7. Create schema migrations for:
   - `electricity_raw`
   - `ev_charger_raw`
   - `hot_water_raw`
   - `weather_raw`
   - `ingestion_runs`
   - `source_status`
8. Add normalized/aggregate views or tables for dashboard reads.

### Phase D — Ingestion and API
9. Build ingestion pipeline:
   - daily fetch
   - normalization
   - idempotent upserts
   - skip invalid rows + error logging
10. Build backend API endpoints for:
   - KPI summary
   - 3 chart datasets
   - source status
   - ingestion audit logs

### Phase E — Frontend MVP dashboard
11. Build auth flow and dashboard shell.
12. Add KPI cards + 3 charts + source status + audit page.
13. Wire frontend data fetching to backend API.

### Phase F — Validation + deployment prep
14. Run full unit/integration test suite.
15. Document local runbook and troubleshooting in `README.md`.
16. Add deployment prep doc for Vercel + hosted Supabase in `docs/deployment/vercel-supabase.md`.

## 6) Endpoint test matrix requirements (minimum)

For each provider endpoint, tests must include:
- Happy path with current credentials.
- Invalid credential path.
- Empty response path.
- Date-range edge case path.
- Basic response schema checks for critical fields used downstream.

Additionally:
- Zaptec: token acquisition + token reuse/expiry behavior.
- Veitur usage-series: irregular interval handling.
- Weather: timezone alignment with dashboard day boundaries.

## 7) Definition of done for local MVP

Local MVP is done when all are true:
- Invited user can sign in and open dashboard.
- All 5 KPIs render from local Supabase-backed data.
- All 3 charts render with expected date windows.
- Daily ingestion runs and writes to Supabase.
- Source status panel shows last successful/failed run per source.
- Audit/log page shows recent ingestion runs.
- Tests pass for endpoint connectivity + core backend + core frontend flows.

## 8) Known open items (must confirm before coding if unclear)

- HS Veitur request contract still needs refinement (currently classified `schema` on smoke test).
- Veitur date windows may need broader backfill range to avoid empty periods.
- Exact invite/auth UX copy and role management depth (if expanded beyond shared-viewer model).

## 9) Resume protocol for next session

When session resumes, execute in this order:

1. Read this file first (`PLAN-HANDOFF.md`).
2. Re-read `API-Endpoints.md`.
3. Confirm `.env` is present but never print values.
4. Check Supabase Docker state.
5. Continue from **Phase D** (ingestion + API implementation).
6. Keep endpoint tests in CI/local checks while refining HS Veitur + Veitur data window behavior.

## 10) Quick resume commands (to run manually tomorrow)

```bash
cd /Users/bsvavarsson/Desktop/OrkunotkunV2
ls -la
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

If Docker shows Supabase services as healthy, continue with scaffold + endpoint tests.
