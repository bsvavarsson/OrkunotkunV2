from __future__ import annotations

import argparse
import asyncio
from datetime import date, datetime, timedelta, UTC
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from app.ingest.db import (
    SourceWriteResult,
    create_ingestion_run,
    finalize_ingestion_run,
    get_connection,
    upsert_electricity_row,
    upsert_ev_charger_row,
    upsert_hot_water_row,
    upsert_weather_row,
    write_source_status,
)
from app.providers.hsveitur import HsVeiturClient
from app.providers.open_meteo import OpenMeteoClient
from app.providers.types import ProviderError
from app.providers.veitur import VeiturClient
from app.providers.zaptec import ZaptecClient
from app.settings import load_provider_settings


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill provider data into local energy tables")
    parser.add_argument("--from", dest="from_date", default=None, help="Start date (YYYY-MM-DD), default Jan 1 this year")
    parser.add_argument("--to", dest="to_date", default=None, help="End date (YYYY-MM-DD), default yesterday")
    return parser.parse_args()


def _resolve_date_range(from_date_input: str | None, to_date_input: str | None) -> tuple[date, date]:
    today = date.today()
    default_from = date(today.year, 1, 1)
    default_to = today - timedelta(days=1)

    from_date = date.fromisoformat(from_date_input) if from_date_input else default_from
    to_date = date.fromisoformat(to_date_input) if to_date_input else default_to

    if from_date > to_date:
        raise ValueError("from date must be <= to date")

    return from_date, to_date


def _parse_datetime(value: Any) -> datetime:
    text = str(value or "").strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    except ValueError:
        parsed = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
        return parsed.replace(tzinfo=UTC)


async def _ingest_hsveitur(from_date: date, to_date: date, run_id: int) -> SourceWriteResult:
    settings = load_provider_settings()
    if not settings.hsveitur_public_token or not settings.hsveitur_private_token or not settings.hsveitur_customer_id:
        return SourceWriteResult(
            source_name="hsveitur",
            status="failed",
            rows_written=0,
            failure_category="config",
            message="Missing HS Veitur credentials in environment",
        )

    client = HsVeiturClient(
        base_url=settings.hsveitur_base_url,
        public_token=settings.hsveitur_public_token,
        private_token=settings.hsveitur_private_token,
        customer_id=settings.hsveitur_customer_id,
    )

    try:
        payload = await client.get_usage_data(date_from=from_date, date_to=to_date)
    except ProviderError as error:
        return SourceWriteResult(
            source_name="hsveitur",
            status="failed",
            rows_written=0,
            failure_category=str(error.category),
            message=error.message,
        )

    usage_rows = payload.get("UsageData", []) if isinstance(payload, dict) else payload
    if not isinstance(usage_rows, list) or not usage_rows:
        return SourceWriteResult(
            source_name="hsveitur",
            status="empty",
            rows_written=0,
            message="No usage rows in payload",
        )

    rows_written = 0
    with get_connection() as connection:
        for row in usage_rows:
            if not isinstance(row, dict):
                continue
            upsert_electricity_row(connection, row=row, run_id=run_id)
            rows_written += 1
        connection.commit()

    return SourceWriteResult(
        source_name="hsveitur",
        status="success" if rows_written else "empty",
        rows_written=rows_written,
        details={"raw_rows": len(usage_rows)},
    )


async def _ingest_veitur(from_date: date, to_date: date, run_id: int) -> SourceWriteResult:
    settings = load_provider_settings()
    if not settings.veitur_api_token or not settings.veitur_permanent_number:
        return SourceWriteResult(
            source_name="veitur",
            status="failed",
            rows_written=0,
            failure_category="config",
            message="Missing Veitur credentials in environment",
        )

    client = VeiturClient(
        base_url=settings.veitur_base_url,
        api_token=settings.veitur_api_token,
        permanent_number=settings.veitur_permanent_number,
    )

    try:
        history_payload = await client.get_reading_history(date_from=from_date, date_to=to_date)
        reading_rows = history_payload.get("meterReading", [])
    except ProviderError as history_error:
        if str(history_error.category) != "empty":
            return SourceWriteResult(
                source_name="veitur",
                status="failed",
                rows_written=0,
                failure_category=str(history_error.category),
                message=history_error.message,
            )
        reading_rows = []

    rows_written = 0
    with get_connection() as connection:
        if reading_rows:
            for row in reading_rows:
                if not isinstance(row, dict):
                    continue
                measured_at = _parse_datetime(row.get("readingDate"))
                interval_days = int(row.get("readingDays") or 0)
                interval_start_at = measured_at - timedelta(days=interval_days)
                interval_end_at = measured_at
                upsert_hot_water_row(
                    connection,
                    permanent_number=settings.veitur_permanent_number,
                    measured_at=measured_at,
                    period_usage_value=row.get("usage"),
                    interval_start_at=interval_start_at,
                    interval_end_at=interval_end_at,
                    interval_days=interval_days,
                    daily_estimation=row.get("dailyEstimation"),
                    reading_value=row.get("readingValue"),
                    usage_unit=None,
                    data_status=0,
                    source_payload=row,
                    run_id=run_id,
                )
                rows_written += 1
            connection.commit()
            return SourceWriteResult(
                source_name="veitur",
                status="success",
                rows_written=rows_written,
                details={"mode": "reading-history", "raw_rows": len(reading_rows)},
            )

        try:
            usage_payload = await client.get_usage_series(date_from=from_date, date_to=to_date)
        except ProviderError as usage_error:
            return SourceWriteResult(
                source_name="veitur",
                status="empty" if str(usage_error.category) == "empty" else "failed",
                rows_written=0,
                failure_category=None if str(usage_error.category) == "empty" else str(usage_error.category),
                message=usage_error.message,
            )

        usage_unit = usage_payload.get("usageUnit") if isinstance(usage_payload, dict) else None
        data_status = usage_payload.get("dataStatus") if isinstance(usage_payload, dict) else None
        data = usage_payload.get("data", []) if isinstance(usage_payload, dict) else []
        for meter_data in data:
            usages = meter_data.get("usages", []) if isinstance(meter_data, dict) else []
            for usage in usages:
                if not isinstance(usage, dict):
                    continue
                measured_at = _parse_datetime(usage.get("timeStamp"))
                upsert_hot_water_row(
                    connection,
                    permanent_number=settings.veitur_permanent_number,
                    measured_at=measured_at,
                    period_usage_value=usage.get("value"),
                    interval_start_at=measured_at,
                    interval_end_at=measured_at,
                    interval_days=0,
                    daily_estimation=None,
                    reading_value=None,
                    usage_unit=usage_unit,
                    data_status=data_status,
                    source_payload=usage,
                    run_id=run_id,
                )
                rows_written += 1
        connection.commit()

    return SourceWriteResult(
        source_name="veitur",
        status="success" if rows_written else "empty",
        rows_written=rows_written,
        details={"mode": "usage-series-fallback", "raw_rows": rows_written},
    )


async def _ingest_zaptec(from_date: date, to_date: date, run_id: int) -> SourceWriteResult:
    settings = load_provider_settings()
    if not settings.zaptec_username or not settings.zaptec_password:
        return SourceWriteResult(
            source_name="zaptec",
            status="failed",
            rows_written=0,
            failure_category="config",
            message="Missing Zaptec credentials in environment",
        )

    client = ZaptecClient(
        base_url=settings.zaptec_base_url,
        token_url=settings.zaptec_token_url,
        username=settings.zaptec_username,
        password=settings.zaptec_password,
    )

    try:
        token = await client.get_access_token()
        payload = await client.get_charge_history(token=token, date_from=from_date, date_to=to_date)
    except ProviderError as error:
        return SourceWriteResult(
            source_name="zaptec",
            status="empty" if str(error.category) == "empty" else "failed",
            rows_written=0,
            failure_category=None if str(error.category) == "empty" else str(error.category),
            message=error.message,
        )

    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        if isinstance(payload.get("Data"), list):
            rows = payload.get("Data", [])
        elif isinstance(payload.get("data"), list):
            rows = payload.get("data", [])
        elif isinstance(payload.get("Items"), list):
            rows = payload.get("Items", [])
        else:
            rows = []
    else:
        rows = []

    if not rows:
        return SourceWriteResult(
            source_name="zaptec",
            status="empty",
            rows_written=0,
            message="No charge history rows in payload",
        )

    rows_written = 0
    with get_connection() as connection:
        for row in rows:
            if not isinstance(row, dict):
                continue
            upsert_ev_charger_row(connection, row=row, run_id=run_id)
            rows_written += 1
        connection.commit()

    return SourceWriteResult(
        source_name="zaptec",
        status="success" if rows_written else "empty",
        rows_written=rows_written,
        details={"raw_rows": len(rows)},
    )


async def _ingest_weather(from_date: date, to_date: date, run_id: int) -> SourceWriteResult:
    settings = load_provider_settings()
    if not settings.location_latitude or not settings.location_longitude:
        return SourceWriteResult(
            source_name="weather",
            status="failed",
            rows_written=0,
            failure_category="config",
            message="Missing location coordinates in environment",
        )

    client = OpenMeteoClient(
        latitude=settings.location_latitude,
        longitude=settings.location_longitude,
        timezone="Atlantic/Reykjavik",
    )

    try:
        payload = await client.get_hourly_weather(date_from=from_date, date_to=to_date)
    except ProviderError as error:
        return SourceWriteResult(
            source_name="weather",
            status="empty" if str(error.category) == "empty" else "failed",
            rows_written=0,
            failure_category=None if str(error.category) == "empty" else str(error.category),
            message=error.message,
        )

    hourly = payload.get("hourly", {}) if isinstance(payload, dict) else {}
    timestamps = hourly.get("time") if isinstance(hourly.get("time"), list) else []
    temperatures = hourly.get("temperature_2m") if isinstance(hourly.get("temperature_2m"), list) else []
    humidities = hourly.get("relative_humidity_2m") if isinstance(hourly.get("relative_humidity_2m"), list) else []
    wind_speeds = hourly.get("wind_speed_10m") if isinstance(hourly.get("wind_speed_10m"), list) else []

    if not timestamps:
        return SourceWriteResult(
            source_name="weather",
            status="empty",
            rows_written=0,
            message="No hourly weather rows in payload",
        )

    rows_written = 0
    with get_connection() as connection:
        for index, timestamp in enumerate(timestamps):
            measured_at = _parse_datetime(timestamp)
            temperature = temperatures[index] if index < len(temperatures) else None
            humidity = humidities[index] if index < len(humidities) else None
            wind_speed = wind_speeds[index] if index < len(wind_speeds) else None

            source_payload = {
                "time": timestamp,
                "temperature_2m": temperature,
                "relative_humidity_2m": humidity,
                "wind_speed_10m": wind_speed,
            }
            upsert_weather_row(
                connection,
                measured_at=measured_at,
                temperature_c=temperature,
                humidity_percent=humidity,
                wind_speed_kmh=wind_speed,
                source_payload=source_payload,
                run_id=run_id,
            )
            rows_written += 1
        connection.commit()

    return SourceWriteResult(
        source_name="weather",
        status="success" if rows_written else "empty",
        rows_written=rows_written,
        details={"raw_rows": rows_written, "granularity": "hourly"},
    )


async def run_backfill(from_date: date, to_date: date) -> list[SourceWriteResult]:
    with get_connection() as connection:
        run_id = create_ingestion_run(connection)

    results: list[SourceWriteResult] = []
    for ingest_func in (_ingest_hsveitur, _ingest_veitur, _ingest_zaptec, _ingest_weather):
        result = await ingest_func(from_date, to_date, run_id)
        results.append(result)
        with get_connection() as connection:
            write_source_status(connection, run_id, result)

    with get_connection() as connection:
        finalize_ingestion_run(connection, run_id, results)

    return results


def main() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    load_dotenv(repo_root / ".env")

    args = _parse_args()
    from_date, to_date = _resolve_date_range(args.from_date, args.to_date)
    results = asyncio.run(run_backfill(from_date=from_date, to_date=to_date))

    print(f"Backfill completed for {from_date.isoformat()} to {to_date.isoformat()}")
    for result in results:
        print(
            f"- {result.source_name}: status={result.status}, rows_written={result.rows_written}"
            + (f", message={result.message}" if result.message else "")
        )


if __name__ == "__main__":
    main()
