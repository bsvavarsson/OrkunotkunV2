from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, UTC
import json
import os
from typing import Any

import psycopg
from psycopg import Connection


@dataclass(slots=True)
class SourceWriteResult:
    source_name: str
    status: str
    rows_written: int
    message: str | None = None
    failure_category: str | None = None
    details: dict[str, Any] | None = None


def get_connection() -> Connection:
    host = os.getenv("SUPABASE_DB_HOST", "127.0.0.1")
    port = os.getenv("SUPABASE_DB_PORT", "54322")
    database = os.getenv("SUPABASE_DB_NAME", "postgres")
    user = os.getenv("SUPABASE_DB_USER", "postgres")
    password = os.getenv("SUPABASE_DB_PASSWORD", "postgres")
    connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    return psycopg.connect(connection_string)


def create_ingestion_run(connection: Connection) -> int:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            insert into energy.ingestion_runs (status)
            values ('running')
            returning id
            """
        )
        run_id = cursor.fetchone()[0]
    connection.commit()
    return int(run_id)


def finalize_ingestion_run(connection: Connection, run_id: int, source_results: list[SourceWriteResult]) -> None:
    success_count = sum(1 for result in source_results if result.status == "success")
    failure_count = sum(1 for result in source_results if result.status == "failed")
    has_partial_or_empty = any(result.status in {"partial", "empty"} for result in source_results)

    if failure_count and success_count:
        final_status = "partial_success"
    elif failure_count and not success_count:
        final_status = "failed"
    elif has_partial_or_empty:
        final_status = "partial_success"
    else:
        final_status = "success"

    details = {
        "finalized_at": datetime.now(UTC).isoformat(),
        "source_results": [
            {
                "source": result.source_name,
                "status": result.status,
                "rows_written": result.rows_written,
                "failure_category": result.failure_category,
                "message": result.message,
                "details": result.details or {},
            }
            for result in source_results
        ],
    }

    with connection.cursor() as cursor:
        cursor.execute(
            """
            update energy.ingestion_runs
            set
              finished_at = now(),
              status = %s,
              source_count = %s,
              success_count = %s,
              failure_count = %s,
              details = %s::jsonb
            where id = %s
            """,
            (final_status, len(source_results), success_count, failure_count, json.dumps(details), run_id),
        )
    connection.commit()


def write_source_status(connection: Connection, run_id: int, result: SourceWriteResult) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            insert into energy.source_status (
              source_name,
              status,
              failure_category,
              message,
              run_id,
              details
            ) values (%s, %s, %s, %s, %s, %s::jsonb)
            """,
            (
                result.source_name,
                result.status,
                result.failure_category,
                result.message,
                run_id,
                json.dumps(result.details or {"rows_written": result.rows_written}),
            ),
        )
    connection.commit()


def upsert_electricity_row(connection: Connection, row: dict[str, Any], run_id: int) -> bool:
    measured_at = _parse_timestamp(row.get("date"))
    meter_id = str(row.get("meter_id") or "unknown")

    with connection.cursor() as cursor:
        cursor.execute(
            """
            insert into energy.electricity_raw (
              source,
              meter_id,
              delivery_point_name,
              measured_at,
              delta_kwh,
              index_value,
              ambient_temperature_c,
              unit_code,
              utility_type,
              source_payload,
              ingestion_run_id
            ) values (
              'hsveitur', %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s
            )
            on conflict (source, meter_id, measured_at)
            do update set
              delivery_point_name = excluded.delivery_point_name,
              delta_kwh = excluded.delta_kwh,
              index_value = excluded.index_value,
              ambient_temperature_c = excluded.ambient_temperature_c,
              unit_code = excluded.unit_code,
              utility_type = excluded.utility_type,
              source_payload = excluded.source_payload,
              ingestion_run_id = excluded.ingestion_run_id
            """,
            (
                meter_id,
                row.get("delivery_point_name"),
                measured_at,
                row.get("delta_value"),
                row.get("index_value"),
                row.get("temperature"),
                row.get("unitcode"),
                row.get("type_data") or row.get("type"),
                json.dumps(row),
                run_id,
            ),
        )
    return True


def upsert_hot_water_row(
    connection: Connection,
    permanent_number: str,
    measured_at: datetime,
    period_usage_value: float | int | None,
    interval_start_at: datetime,
    interval_end_at: datetime,
    interval_days: int,
    daily_estimation: float | int | None,
    reading_value: float | int | None,
    usage_unit: str | None,
    data_status: int | None,
    source_payload: dict[str, Any],
    run_id: int,
) -> bool:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            insert into energy.hot_water_raw (
              source,
              permanent_number,
              measured_at,
              usage_value,
                            period_usage_value,
                            interval_start_at,
                            interval_end_at,
                            interval_days,
                            daily_estimation,
                            reading_value,
              usage_unit,
              data_status,
              source_payload,
              ingestion_run_id
            ) values (
                            'veitur',
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s::jsonb,
                            %s
            )
            on conflict (source, permanent_number, measured_at)
            do update set
              usage_value = excluded.usage_value,
                            period_usage_value = excluded.period_usage_value,
                            interval_start_at = excluded.interval_start_at,
                            interval_end_at = excluded.interval_end_at,
                            interval_days = excluded.interval_days,
                            daily_estimation = excluded.daily_estimation,
                            reading_value = excluded.reading_value,
              usage_unit = excluded.usage_unit,
              data_status = excluded.data_status,
              source_payload = excluded.source_payload,
              ingestion_run_id = excluded.ingestion_run_id
            """,
            (
                permanent_number,
                measured_at,
                period_usage_value,
                period_usage_value,
                interval_start_at,
                interval_end_at,
                interval_days,
                daily_estimation,
                reading_value,
                usage_unit,
                data_status,
                json.dumps(source_payload),
                run_id,
            ),
        )
    return True


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)

    text = str(value or "").strip()
    if not text:
        raise ValueError("Missing timestamp value")

    text = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    except ValueError:
        parsed = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
        return parsed.replace(tzinfo=UTC)
