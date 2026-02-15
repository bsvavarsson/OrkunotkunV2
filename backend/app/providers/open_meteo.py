from __future__ import annotations

from datetime import date

import httpx

from app.providers.types import FailureCategory, ProviderError, raise_for_response


class OpenMeteoClient:
    def __init__(self, latitude: str, longitude: str, timezone: str = "Atlantic/Reykjavik") -> None:
        self._latitude = latitude
        self._longitude = longitude
        self._timezone = timezone
        self._base_url = "https://archive-api.open-meteo.com/v1/archive"

    async def get_hourly_weather(self, date_from: date, date_to: date) -> dict:
        params = {
            "latitude": self._latitude,
            "longitude": self._longitude,
            "start_date": date_from.isoformat(),
            "end_date": date_to.isoformat(),
            "timezone": self._timezone,
            "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self._base_url, params=params)
        except httpx.RequestError as exc:
            raise ProviderError("open_meteo", FailureCategory.NETWORK, str(exc)) from exc

        raise_for_response("open_meteo", response)
        payload = response.json()

        if not isinstance(payload, dict):
            raise ProviderError("open_meteo", FailureCategory.SCHEMA, "Unexpected response shape")

        hourly = payload.get("hourly")
        if not isinstance(hourly, dict) or not hourly.get("time"):
            raise ProviderError("open_meteo", FailureCategory.EMPTY, "Missing hourly time series")

        return payload
