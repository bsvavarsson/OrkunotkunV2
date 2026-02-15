# Integration Test Matrix (Phase B)

## Providers

### Veitur (hot water)
- Happy path: `GET /api/meter/usage-series` with valid bearer token and permanent number.
- Fallback strategy: if `usage-series` returns empty, test `GET /api/meter/reading-history`; if still empty, validate `GET /api/meter/info` for active meter presence.
- Invalid credentials: bad bearer token should classify as `auth`.
- Empty response: `dataStatus=521` should classify as `empty`.
- Date edge case: short range (last 7 days) and irregular interval payload acceptance.
- Schema checks: `dataStatus`, `usageUnit`, and usage time/value arrays.

### HS Veitur (electricity)
- Happy path: `POST Expectus/UsageData` with snake_case query params (`public_token`, `private_token`, `customer_id`, `datefrom`, `dateto`, `page_size`, `page`).
- Pagination: iterate pages until `Info.NextPage` is `None`; do not stop at page 1.
- Invalid credentials: invalid token pair should classify as `auth`/`schema` based on API behavior.
- Empty response: empty list/object should classify as `empty`.
- Date edge case: test with narrow and wider ranges.
- Schema checks: expect `Info` metadata and `UsageData` entries with `date`, `delta_value`, `meter_id`, `unitcode`.

### Zaptec (EV)
- Happy path: obtain OAuth token, then call `/api/chargers` and `/api/chargehistory`.
- Invalid credentials: wrong password must classify as `auth` (or `rate_limit` if throttled).
- Empty response: no sessions in selected date window should classify as `empty`.
- Date edge case: verify `from`/`to` ranges are accepted.
- Schema checks: token object has `access_token`; list payload returns object/list.

### Open-Meteo (weather)
- Happy path: archive endpoint with location and hourly fields.
- Invalid input: malformed coordinates should classify as `schema`.
- Empty response: missing `hourly.time` should classify as `empty`.
- Date edge case: same-day and 7-day ranges.
- Schema checks: hourly arrays include `time`, `temperature_2m`, `relative_humidity_2m`, `wind_speed_10m`.

## Evidence output

- Redacted evidence files are written to `docs/integration-evidence/*-latest.json`.
- Sensitive keys (`token`, `authorization`, `password`, `secret`, API keys) are masked.
