from __future__ import annotations

from datetime import date

import httpx

from app.providers.types import FailureCategory, ProviderError, raise_for_response


class ZaptecClient:
    def __init__(self, base_url: str, token_url: str, username: str, password: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._token_url = token_url
        self._username = username
        self._password = password

    async def get_access_token(self) -> str:
        data = {
            "grant_type": "password",
            "username": self._username,
            "password": self._password,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self._token_url, data=data)
        except httpx.RequestError as exc:
            raise ProviderError("zaptec", FailureCategory.NETWORK, str(exc)) from exc

        raise_for_response("zaptec", response)
        payload = response.json()

        access_token = payload.get("access_token") if isinstance(payload, dict) else None
        if not access_token:
            raise ProviderError("zaptec", FailureCategory.SCHEMA, "Missing access_token in OAuth response")

        return access_token

    async def get_chargers(self, token: str) -> dict | list:
        return await self._get("/api/chargers", token=token)

    async def get_charge_history(self, token: str, date_from: date, date_to: date) -> dict | list:
        params = {
            "from": date_from.isoformat(),
            "to": date_to.isoformat(),
            "pagesize": 50,
        }
        return await self._get("/api/chargehistory", token=token, params=params)

    async def _get(self, path: str, token: str, params: dict | None = None) -> dict | list:
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{self._base_url}{path}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers, params=params)
        except httpx.RequestError as exc:
            raise ProviderError("zaptec", FailureCategory.NETWORK, str(exc)) from exc

        raise_for_response("zaptec", response)
        payload = response.json()

        if payload in ({}, []):
            raise ProviderError("zaptec", FailureCategory.EMPTY, "No rows returned", status_code=200)

        if not isinstance(payload, (dict, list)):
            raise ProviderError("zaptec", FailureCategory.SCHEMA, "Unexpected response shape")

        return payload
