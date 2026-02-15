# Frontend

React + TypeScript dashboard (V1 Option 1 layout):

- 5 KPI cards (Brutto, Netto, EV, Hot Water, Weather)
- Energy hero chart (daily Brutto vs 3-month rolling average)
- Hot-water and EV trend charts
- Source status panel
- Ingestion audit table

## Development

From repository root:

```bash
pnpm install
pnpm --filter @orkunotkun/frontend dev
```

To enable the `Sync data` button, run backend API in a separate terminal:

```bash
cd backend
.venv/bin/uvicorn app.api.main:app --reload --host 127.0.0.1 --port 8000
```

## Environment

Frontend reads Supabase through:

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`

Alternative key aliases also supported:

- `VITE_SUPABASE_PUBLISHABLE_KEY`
- `SUPABASE_PUBLISHABLE_KEY`

It also accepts root `.env` fallbacks:

- `SUPABASE_API_URL`
- `SUPABASE_ANON_KEY`
- `VITE_BACKEND_URL`

Values are normalized (trimmed, wrapping quotes removed) to prevent copy/paste formatting errors.

Dashboard reads use `public` wrapper views (`dashboard_daily`, `source_status`, `ingestion_runs`) that map to `energy.*` internally.

If not set, the app runs with built-in mock data.
