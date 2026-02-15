from __future__ import annotations

from datetime import date

import httpx

from app.providers.types import FailureCategory, ProviderError, raise_for_response


class VeiturClient:
    def __init__(self, base_url: str, api_token: str, permanent_number: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_token = api_token
        self._permanent_number = permanent_number

    async def get_usage_series(self, date_from: date, date_to: date) -> dict:
        url = f"{self._base_url}/api/meter/usage-series"
        headers = {"Authorization": f"Bearer {self._api_token}"}
        params = {
            "PermanentNumber": self._permanent_number,
            "DateFrom": date_from.isoformat(),
            "DateTo": date_to.isoformat(),
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers, params=params)
        except httpx.RequestError as exc:
            raise ProviderError("veitur", FailureCategory.NETWORK, str(exc)) from exc

        raise_for_response("veitur", response)
        payload = response.json()

        if isinstance(payload, dict) and payload.get("dataStatus") == 521:
            raise ProviderError("veitur", FailureCategory.EMPTY, "No data found", status_code=200)

        if not isinstance(payload, dict):
            raise ProviderError("veitur", FailureCategory.SCHEMA, "Unexpected response shape")

        return payload
