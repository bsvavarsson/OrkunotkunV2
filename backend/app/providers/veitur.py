from __future__ import annotations

from datetime import date, datetime, time

import httpx

from app.providers.types import FailureCategory, ProviderError, raise_for_response


VEITUR_DATA_STATUS_OK = 0
VEITUR_DATA_STATUS_NO_VALUES = 500
VEITUR_DATA_STATUS_EARLIER_AND_LATER_MISSING = 501
VEITUR_DATA_STATUS_EARLIER_MISSING = 502
VEITUR_DATA_STATUS_LATER_MISSING = 503
VEITUR_DATA_STATUS_METER_NOT_FOUND = 520
VEITUR_DATA_STATUS_NO_DATA = 521


def _to_veitur_datetime(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M")


class VeiturClient:
    def __init__(self, base_url: str, api_token: str, permanent_number: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_token = api_token
        self._permanent_number = permanent_number

    async def get_usage_series(self, date_from: date, date_to: date) -> dict:
        date_from_dt = datetime.combine(date_from, time.min)
        date_to_dt = datetime.combine(date_to, time.max)
        params = {
            "PermanentNumber": self._permanent_number,
            "DateFrom": _to_veitur_datetime(date_from_dt),
            "DateTo": _to_veitur_datetime(date_to_dt),
        }
        payload = await self._get("/api/meter/usage-series", params=params)
        self._raise_for_data_status(payload)
        return payload

    async def get_reading_history(self, date_from: date, date_to: date) -> dict:
        date_from_dt = datetime.combine(date_from, time.min)
        date_to_dt = datetime.combine(date_to, time.max)
        params = {
            "PermanentNumber": self._permanent_number,
            "DateFrom": _to_veitur_datetime(date_from_dt),
            "DateTo": _to_veitur_datetime(date_to_dt),
        }
        payload = await self._get("/api/meter/reading-history", params=params)

        if not isinstance(payload.get("meterReading"), list) or not payload.get("meterReading"):
            raise ProviderError("veitur", FailureCategory.EMPTY, "No reading history found", status_code=200)

        return payload

    async def get_meter_info(self, date_from: date, date_to: date) -> list[dict]:
        date_from_dt = datetime.combine(date_from, time.min)
        date_to_dt = datetime.combine(date_to, time.max)
        params = {
            "DateFrom": _to_veitur_datetime(date_from_dt),
            "DateTo": _to_veitur_datetime(date_to_dt),
        }
        payload = await self._get("/api/meter/info", params=params)

        if not isinstance(payload, list):
            raise ProviderError("veitur", FailureCategory.SCHEMA, "Unexpected meter info response shape")

        return payload

    async def _get(self, path: str, params: dict[str, str]) -> dict | list[dict]:
        url = f"{self._base_url}{path}"
        headers = {"Authorization": f"Bearer {self._api_token}"}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers, params=params)
        except httpx.RequestError as exc:
            raise ProviderError("veitur", FailureCategory.NETWORK, str(exc)) from exc

        raise_for_response("veitur", response)
        payload = response.json()

        if not isinstance(payload, (dict, list)):
            raise ProviderError("veitur", FailureCategory.SCHEMA, "Unexpected response shape")

        return payload

    def _raise_for_data_status(self, payload: dict) -> None:
        status = payload.get("dataStatus")
        if status is None:
            raise ProviderError("veitur", FailureCategory.SCHEMA, "Missing dataStatus in usage-series response")

        if status == VEITUR_DATA_STATUS_OK:
            return

        if status in {
            VEITUR_DATA_STATUS_NO_VALUES,
            VEITUR_DATA_STATUS_EARLIER_AND_LATER_MISSING,
            VEITUR_DATA_STATUS_EARLIER_MISSING,
            VEITUR_DATA_STATUS_LATER_MISSING,
            VEITUR_DATA_STATUS_NO_DATA,
        }:
            raise ProviderError("veitur", FailureCategory.EMPTY, f"No usable data (dataStatus={status})", status_code=200)

        if status == VEITUR_DATA_STATUS_METER_NOT_FOUND:
            raise ProviderError("veitur", FailureCategory.SCHEMA, "Meter not found", status_code=200)

        raise ProviderError("veitur", FailureCategory.SCHEMA, f"Unhandled dataStatus={status}", status_code=200)
