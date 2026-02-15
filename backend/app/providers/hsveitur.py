from __future__ import annotations

from datetime import date, datetime, time

import httpx

from app.providers.types import FailureCategory, ProviderError, raise_for_response


class HsVeiturClient:
    def __init__(self, base_url: str, public_token: str, private_token: str, customer_id: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._public_token = public_token
        self._private_token = private_token
        self._customer_id = customer_id

    async def get_usage_data(self, date_from: date, date_to: date) -> dict | list:
        page = 1
        max_pages = 50
        all_usage_rows: list[dict] = []
        total_rows_hint: int | None = None

        while page <= max_pages:
            payload = await self._get_usage_data_page(date_from=date_from, date_to=date_to, page=page)

            if isinstance(payload, dict) and payload.get("ErrorCode"):
                error_message = str(payload.get("message", "HS Veitur API returned an error"))
                lowered = error_message.lower()
                if "invalid public_token" in lowered or "invalid private_token" in lowered or "token" in lowered:
                    raise ProviderError(
                        "hsveitur",
                        FailureCategory.AUTH,
                        error_message,
                        status_code=200,
                    )

                raise ProviderError(
                    "hsveitur",
                    FailureCategory.SCHEMA,
                    error_message,
                    status_code=200,
                )

            if payload in ({}, []):
                raise ProviderError("hsveitur", FailureCategory.EMPTY, "No usage rows returned", status_code=200)

            if not isinstance(payload, dict):
                raise ProviderError("hsveitur", FailureCategory.SCHEMA, "Unexpected response shape")

            info = payload.get("Info") if isinstance(payload.get("Info"), dict) else {}
            usage_rows = payload.get("UsageData") if isinstance(payload.get("UsageData"), list) else None
            if usage_rows is None:
                raise ProviderError("hsveitur", FailureCategory.SCHEMA, "Missing UsageData list in response")

            if total_rows_hint is None and info.get("TotalNoRows") is not None:
                try:
                    total_rows_hint = int(info.get("TotalNoRows"))
                except (TypeError, ValueError):
                    total_rows_hint = None

            all_usage_rows.extend(row for row in usage_rows if isinstance(row, dict))

            next_page = str(info.get("NextPage") or "None")
            if next_page.lower() == "none" or not usage_rows:
                break

            page += 1

        if not all_usage_rows:
            raise ProviderError("hsveitur", FailureCategory.EMPTY, "No usage rows returned after pagination", status_code=200)

        return {
            "Info": {
                "TotalNoRows": total_rows_hint if total_rows_hint is not None else len(all_usage_rows),
                "NextPage": "None",
                "FetchedPages": page,
            },
            "UsageData": all_usage_rows,
        }

    async def _get_usage_data_page(self, date_from: date, date_to: date, page: int) -> dict | list:
        url = f"{self._base_url}/Expectus/UsageData"
        date_from_datetime = datetime.combine(date_from, time.min).strftime("%Y-%m-%dT%H:%M:%S.000")
        date_to_datetime = datetime.combine(date_to, time.max).strftime("%Y-%m-%dT%H:%M:%S.999")

        query_params = {
            "public_token": self._public_token,
            "private_token": self._private_token,
            "customer_id": self._customer_id,
            "datefrom": date_from_datetime,
            "dateto": date_to_datetime,
            "page_size": "1000",
            "page": str(page),
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, params=query_params)
        except httpx.RequestError as exc:
            raise ProviderError("hsveitur", FailureCategory.NETWORK, str(exc)) from exc

        raise_for_response("hsveitur", response)
        payload = response.json()

        if not isinstance(payload, (dict, list)):
            raise ProviderError("hsveitur", FailureCategory.SCHEMA, "Unexpected response shape")

        return payload
