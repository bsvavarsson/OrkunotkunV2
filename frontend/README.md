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

## Environment

Frontend reads Supabase through:

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`

If not set, the app runs with built-in mock data.
