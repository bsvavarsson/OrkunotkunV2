from __future__ import annotations

from datetime import date, timedelta
import os

import pytest

from app.providers.evidence import write_integration_evidence
from app.providers.hsveitur import HsVeiturClient
from app.providers.open_meteo import OpenMeteoClient
from app.providers.types import FailureCategory, ProviderError
from app.providers.veitur import VeiturClient
from app.providers.zaptec import ZaptecClient
from app.settings import load_provider_settings


pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


def _last_seven_days() -> tuple[date, date]:
    today = date.today()
    return today - timedelta(days=7), today - timedelta(days=1)


def _from_january_first_to_yesterday() -> tuple[date, date]:
    today = date.today()
    return date(today.year, 1, 1), today - timedelta(days=1)


def _has_values(*values: str | None) -> bool:
    return all(value is not None and value.strip() for value in values)


@pytest.mark.integration
async def test_veitur_usage_series_smoke() -> None:
    settings = load_provider_settings()
    if not _has_values(settings.veitur_api_token, settings.veitur_permanent_number):
        pytest.skip("Missing VEITUR credentials")

    client = VeiturClient(
        base_url=settings.veitur_base_url,
        api_token=settings.veitur_api_token or "",
        permanent_number=settings.veitur_permanent_number or "",
    )
    date_from, date_to = _from_january_first_to_yesterday()

    fallback_used = None
    try:
        payload = await client.get_usage_series(date_from=date_from, date_to=date_to)
        assert "dataStatus" in payload
        result = {
            "status": "ok",
            "path": "usage-series",
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "data_status": payload.get("dataStatus"),
        }
    except ProviderError as usage_error:
        if usage_error.category != FailureCategory.EMPTY:
            write_integration_evidence(
                "veitur",
                {
                    "status": "classified_failure",
                    "path": "usage-series",
                    "category": usage_error.category,
                    "status_code": usage_error.status_code,
                    "message": usage_error.message,
                    "date_from": date_from.isoformat(),
                    "date_to": date_to.isoformat(),
                },
            )
            raise

        try:
            fallback_payload = await client.get_reading_history(date_from=date_from, date_to=date_to)
            fallback_used = "reading-history"
            result = {
                "status": "ok",
                "path": "reading-history",
                "date_from": date_from.isoformat(),
                "date_to": date_to.isoformat(),
                "reading_count": len(fallback_payload.get("meterReading", [])),
            }
        except ProviderError as history_error:
            if history_error.category != FailureCategory.EMPTY:
                write_integration_evidence(
                    "veitur",
                    {
                        "status": "classified_failure",
                        "path": "reading-history",
                        "category": history_error.category,
                        "status_code": history_error.status_code,
                        "message": history_error.message,
                        "date_from": date_from.isoformat(),
                        "date_to": date_to.isoformat(),
                    },
                )
                raise

            meter_info = await client.get_meter_info(date_from=date_from, date_to=date_to)
            fallback_used = "meter-info"
            if not meter_info:
                write_integration_evidence(
                    "veitur",
                    {
                        "status": "classified_failure",
                        "path": "usage-series->reading-history->meter-info",
                        "category": FailureCategory.EMPTY,
                        "message": "No usage-series data, no reading-history, and no active meter-info in date range",
                        "date_from": date_from.isoformat(),
                        "date_to": date_to.isoformat(),
                    },
                )
                pytest.skip("Veitur has no data from usage-series/reading-history in selected range")

            result = {
                "status": "ok",
                "path": "meter-info",
                "date_from": date_from.isoformat(),
                "date_to": date_to.isoformat(),
                "meter_count": len(meter_info),
            }

    if fallback_used:
        result["fallback_used"] = fallback_used

    write_integration_evidence("veitur", result)


@pytest.mark.integration
async def test_hsveitur_usage_data_smoke() -> None:
    settings = load_provider_settings()
    if not _has_values(settings.hsveitur_public_token, settings.hsveitur_private_token, settings.hsveitur_customer_id):
        pytest.skip("Missing HS Veitur credentials")

    client = HsVeiturClient(
        base_url=settings.hsveitur_base_url,
        public_token=settings.hsveitur_public_token or "",
        private_token=settings.hsveitur_private_token or "",
        customer_id=settings.hsveitur_customer_id or "",
    )
    date_from, date_to = _last_seven_days()
    try:
        payload = await client.get_usage_data(date_from=date_from, date_to=date_to)
    except ProviderError as error:
        write_integration_evidence(
            "hsveitur",
            {
                "status": "classified_failure",
                "category": error.category,
                "status_code": error.status_code,
                "message": error.message,
                "date_from": date_from.isoformat(),
                "date_to": date_to.isoformat(),
            },
        )
        if error.category == FailureCategory.EMPTY:
            pytest.skip("HS Veitur returned no data in selected range")
        raise

    assert isinstance(payload, (dict, list))
    write_integration_evidence(
        "hsveitur",
        {
            "status": "ok",
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "response_type": type(payload).__name__,
        },
    )


@pytest.mark.integration
async def test_zaptec_auth_and_chargers_smoke() -> None:
    settings = load_provider_settings()
    if not _has_values(settings.zaptec_username, settings.zaptec_password):
        pytest.skip("Missing Zaptec credentials")

    client = ZaptecClient(
        base_url=settings.zaptec_base_url,
        token_url=settings.zaptec_token_url,
        username=settings.zaptec_username or "",
        password=settings.zaptec_password or "",
    )
    token = await client.get_access_token()
    assert token

    chargers_payload = await client.get_chargers(token=token)
    assert isinstance(chargers_payload, (dict, list))

    date_from, date_to = _last_seven_days()
    history_payload = await client.get_charge_history(token=token, date_from=date_from, date_to=date_to)
    assert isinstance(history_payload, (dict, list))

    write_integration_evidence(
        "zaptec",
        {
            "status": "ok",
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "chargers_type": type(chargers_payload).__name__,
            "history_type": type(history_payload).__name__,
            "token_present": bool(token),
        },
    )


@pytest.mark.integration
async def test_open_meteo_weather_smoke() -> None:
    settings = load_provider_settings()
    if not _has_values(settings.location_latitude, settings.location_longitude):
        pytest.skip("Missing location coordinates")

    client = OpenMeteoClient(
        latitude=settings.location_latitude or "",
        longitude=settings.location_longitude or "",
        timezone="Atlantic/Reykjavik",
    )
    date_from, date_to = _last_seven_days()
    payload = await client.get_hourly_weather(date_from=date_from, date_to=date_to)

    assert "hourly" in payload
    assert isinstance(payload["hourly"], dict)

    write_integration_evidence(
        "open_meteo",
        {
            "status": "ok",
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "hourly_fields": sorted(payload.get("hourly", {}).keys())[:6],
        },
    )


@pytest.mark.integration
async def test_zaptec_invalid_credentials_classified_as_auth() -> None:
    if os.getenv("RUN_INVALID_AUTH_TESTS") != "1":
        pytest.skip("Set RUN_INVALID_AUTH_TESTS=1 to run invalid-credential tests")

    settings = load_provider_settings()
    if not _has_values(settings.zaptec_username, settings.zaptec_password):
        pytest.skip("Missing Zaptec credentials")

    invalid_client = ZaptecClient(
        base_url=settings.zaptec_base_url,
        token_url=settings.zaptec_token_url,
        username=settings.zaptec_username or "",
        password=f"{settings.zaptec_password}__invalid",
    )

    with pytest.raises(ProviderError) as exc_info:
        await invalid_client.get_access_token()

    assert exc_info.value.category in {FailureCategory.AUTH, FailureCategory.RATE_LIMIT}
