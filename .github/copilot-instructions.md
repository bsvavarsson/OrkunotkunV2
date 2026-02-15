# Copilot Instructions for OrkunotkunV2

## Project defaults

- Backend: Python + FastAPI
- Frontend: React + TypeScript
- Database: Supabase (PostgreSQL)
- Timezone/locale: `Atlantic/Reykjavik`, `is-IS`

## Non-negotiable rules

- Never expose `.env` secret values in code, logs, docs, tests, or commits.
- Always keep `.env` untracked and use `.env.example` placeholders.
- Endpoint connectivity tests must be implemented before app feature expansion.
- Normalize provider data into canonical domain models before database writes.
- Keep implementation minimal and aligned with `PLAN-HANDOFF.md`.

## Coding conventions

- Use explicit, descriptive names (no one-letter identifiers).
- Keep modules focused and small.
- Add type hints in Python code.
- Add unit tests for parsing/normalization and integration tests for provider calls.
- Log with structured context and redact credentials/tokens.

## Data modeling defaults

- Raw tables by source: electricity, ev_charger, hot_water, weather.
- Track ingestion run metadata and source health per run.
- Derive `netto` as `brutto - ev_charger` for v1.
