from __future__ import annotations

from datetime import date

import httpx

from app.providers.types import FailureCategory, ProviderError, raise_for_response


class HsVeiturClient:
    def __init__(self, base_url: str, public_token: str, private_token: str, customer_id: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._public_token = public_token
        self._private_token = private_token
        self._customer_id = customer_id

    async def get_usage_data(self, date_from: date, date_to: date) -> dict | list:
        url = f"{self._base_url}/Expectus/UsageData"
        params = {
            "publicToken": self._public_token,
            "privateToken": self._private_token,
            "customerId": self._customer_id,
            "dateFrom": date_from.isoformat(),
            "dateTo": date_to.isoformat(),
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
        except httpx.RequestError as exc:
            raise ProviderError("hsveitur", FailureCategory.NETWORK, str(exc)) from exc

        raise_for_response("hsveitur", response)
        payload = response.json()

        if payload in ({}, []):
            raise ProviderError("hsveitur", FailureCategory.EMPTY, "No usage rows returned", status_code=200)

        if not isinstance(payload, (dict, list)):
            raise ProviderError("hsveitur", FailureCategory.SCHEMA, "Unexpected response shape")

        return payload
