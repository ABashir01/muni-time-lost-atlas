"""Load real historic 511 RG stop_observations archives into raw.stop_observations."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from io import StringIO, TextIOWrapper
import json
from pathlib import Path
import re
from typing import Any, Mapping
import zipfile
from zoneinfo import ZoneInfo

import psycopg

from muni_lta_pipeline.gtfs_static_fixture_ingest import (
    build_postgres_connection_url,
    docker_compose_psql_args,
    ensure_db_service,
    execute_sql_file,
    get_postgres_settings,
    run_command,
    wait_for_database,
)
from muni_lta_pipeline.historic_rg_feed_fetch import STOP_OBSERVATIONS_FILENAME
from muni_lta_pipeline.historic_stop_observations_fixture_ingest import (
    DDL_FILE,
    METADATA_COLUMNS,
    TABLE_NAME,
    TABLE_COLUMNS,
    truncate_stop_observations,
)


DEFAULT_LOCAL_TIMEZONE = "America/Los_Angeles"
DEFAULT_INSERT_BATCH_SIZE = 50000
SERVICE_DATE_COMPACT_PATTERN = re.compile(r"^\d{8}$")
SERVICE_DAY_TIME_PATTERN = re.compile(r"^(?P<hours>\d{1,2}):(?P<minutes>\d{2}):(?P<seconds>\d{2})$")
REQUIRED_ARCHIVE_COLUMNS = (
    "service_date",
    "trip_id",
    "stop_sequence",
    "to_stop_id",
    "observed_arrival_time",
)
ARCHIVE_STAGE_TABLE = "stop_observations_archive_stage"
ARCHIVE_STAGE_COLUMNS = (
    "service_date_text",
    "trip_id",
    "stop_id",
    "stop_sequence_text",
    "observed_arrival_time",
    "source_system",
    "feed_scope",
    "operator_id",
    "snapshot_label",
    "ingested_at",
)


@dataclass(frozen=True)
class HistoricStopObservationsArchiveLoadResult:
    inserted_row_count: int
    skipped_missing_required_count: int
    snapshot_label: str
    metadata_path: Path
    artifact_path: Path


def parse_compact_service_date(value: str) -> date:
    if not SERVICE_DATE_COMPACT_PATTERN.fullmatch(value):
        raise ValueError(
            f"service_date must be YYYYMMDD in the historic archive; received {value!r}."
        )

    try:
        return date(
            int(value[0:4]),
            int(value[4:6]),
            int(value[6:8]),
        )
    except ValueError as exc:
        raise ValueError(
            f"service_date must be YYYYMMDD in the historic archive; received {value!r}."
        ) from exc


def _validate_compact_service_date_text(value: str) -> None:
    if not SERVICE_DATE_COMPACT_PATTERN.fullmatch(value):
        raise ValueError(
            f"service_date must be YYYYMMDD in the historic archive; received {value!r}."
        )


def parse_service_day_observed_arrival_timestamp(
    service_date_value: str,
    observed_arrival_time: str,
    *,
    local_timezone: str = DEFAULT_LOCAL_TIMEZONE,
) -> datetime:
    parsed_service_date = parse_compact_service_date(service_date_value)
    match = SERVICE_DAY_TIME_PATTERN.fullmatch(observed_arrival_time)
    if match is None:
        raise ValueError(
            "observed_arrival_time must be HH:MM:SS in the historic archive."
        )

    hours = int(match.group("hours"))
    minutes = int(match.group("minutes"))
    seconds = int(match.group("seconds"))

    if minutes > 59 or seconds > 59:
        raise ValueError(
            "observed_arrival_time must be HH:MM:SS in the historic archive."
        )

    tz = ZoneInfo(local_timezone)
    service_day_start = datetime.combine(parsed_service_date, time(0, 0), tzinfo=tz)
    return service_day_start + timedelta(
        hours=hours,
        minutes=minutes,
        seconds=seconds,
    )


def load_historic_archive_metadata(metadata_path: Path) -> dict[str, Any]:
    if not metadata_path.exists():
        raise FileNotFoundError(f"Historic acquisition metadata file not found: {metadata_path}")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    required_fields = (
        "source_system",
        "feed_scope",
        "operator_id",
        "artifact_filename",
        "requested_historic_month",
        "requested_historic_value",
        "requested_stop_observations",
        "stop_observations_present",
    )
    missing_fields = [field for field in required_fields if field not in metadata]
    if missing_fields:
        raise ValueError(
            "Historic acquisition metadata is missing required fields: "
            + ", ".join(missing_fields)
        )

    if not metadata["requested_stop_observations"]:
        raise ValueError(
            "Historic acquisition metadata must come from a '-so' archive request."
        )

    if not metadata["stop_observations_present"]:
        raise ValueError(
            "Historic acquisition metadata must confirm stop_observations.txt is present."
        )

    return metadata


def resolve_archive_artifact_path(metadata_path: Path, metadata: Mapping[str, Any]) -> Path:
    artifact_filename = str(metadata["artifact_filename"]).strip()
    if not artifact_filename:
        raise ValueError("Historic acquisition metadata must include artifact_filename.")
    artifact_path = metadata_path.parent / artifact_filename
    if not artifact_path.exists():
        raise FileNotFoundError(f"Historic archive zip not found: {artifact_path}")
    return artifact_path


def build_archive_snapshot_label(metadata: Mapping[str, Any]) -> str:
    artifact_stem = Path(str(metadata["artifact_filename"])).stem
    return f"archive_{artifact_stem}"


def _validate_archive_headers(fieldnames: list[str] | None) -> None:
    if fieldnames is None:
        raise ValueError("Historic stop_observations.txt has no header row.")

    missing_headers = [
        column for column in REQUIRED_ARCHIVE_COLUMNS if column not in fieldnames
    ]
    if missing_headers:
        raise ValueError(
            "Historic stop_observations.txt is missing required columns: "
            + ", ".join(missing_headers)
        )


def _transform_archive_row(
    raw_row: Mapping[str, str | None],
    metadata: Mapping[str, str | None],
    *,
    local_timezone: str,
) -> tuple[str, ...] | None:
    service_date_value = (raw_row.get("service_date") or "").strip()
    trip_id = (raw_row.get("trip_id") or "").strip()
    stop_id = (raw_row.get("to_stop_id") or "").strip()
    stop_sequence = (raw_row.get("stop_sequence") or "").strip()
    observed_arrival_time = (raw_row.get("observed_arrival_time") or "").strip()

    if not service_date_value or not trip_id or not stop_id or not stop_sequence:
        raise ValueError(
            "Historic stop_observations rows must populate service_date, trip_id, to_stop_id, and stop_sequence."
        )

    if not observed_arrival_time:
        return None

    _validate_compact_service_date_text(service_date_value)
    match = SERVICE_DAY_TIME_PATTERN.fullmatch(observed_arrival_time)
    if match is None:
        raise ValueError(
            "observed_arrival_time must be HH:MM:SS in the historic archive."
        )

    minutes = int(match.group("minutes"))
    seconds = int(match.group("seconds"))
    if minutes > 59 or seconds > 59:
        raise ValueError(
            "observed_arrival_time must be HH:MM:SS in the historic archive."
        )

    _ = local_timezone
    return (
        service_date_value,
        trip_id,
        stop_id,
        stop_sequence,
        observed_arrival_time,
        metadata["source_system"] or "",
        metadata["feed_scope"] or "",
        metadata["operator_id"] or "",
        metadata["snapshot_label"] or "",
        metadata["ingested_at"] or "",
    )


def _copy_archive_rows(
    connection: psycopg.Connection[Any],
    rows: list[tuple[str, ...]],
    *,
    local_timezone: str,
) -> int:
    if not rows:
        return 0

    copy_sql = (
        f"COPY {ARCHIVE_STAGE_TABLE} ({', '.join(ARCHIVE_STAGE_COLUMNS)}) "
        "FROM STDIN WITH (FORMAT CSV)"
    )
    csv_buffer = StringIO()
    writer = csv.writer(csv_buffer, lineterminator="\n")
    for row in rows:
        writer.writerow(row)

    with connection.cursor() as cursor:
        with cursor.copy(copy_sql) as copy:
            copy.write(csv_buffer.getvalue())
        cursor.execute(
            f"""
            INSERT INTO {TABLE_NAME} ({', '.join([*TABLE_COLUMNS, *METADATA_COLUMNS])})
            SELECT
                to_date(service_date_text, 'YYYYMMDD') as service_date,
                trip_id,
                stop_id,
                stop_sequence_text::integer as stop_sequence,
                observed_arrival_time,
                (
                    (to_date(service_date_text, 'YYYYMMDD')::timestamp AT TIME ZONE %s)
                    + make_interval(
                        hours => split_part(observed_arrival_time, ':', 1)::integer,
                        mins => split_part(observed_arrival_time, ':', 2)::integer,
                        secs => split_part(observed_arrival_time, ':', 3)::integer
                    )
                ) as observed_arrival_ts,
                source_system,
                feed_scope,
                nullif(operator_id, '') as operator_id,
                snapshot_label,
                ingested_at
            FROM {ARCHIVE_STAGE_TABLE};
            """,
            (local_timezone,),
        )
        cursor.execute(f"TRUNCATE TABLE {ARCHIVE_STAGE_TABLE};")
    return len(rows)


def _ensure_archive_stage_table(connection: psycopg.Connection[Any]) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            CREATE TEMP TABLE IF NOT EXISTS {ARCHIVE_STAGE_TABLE} (
                service_date_text TEXT NOT NULL,
                trip_id TEXT NOT NULL,
                stop_id TEXT NOT NULL,
                stop_sequence_text TEXT NOT NULL,
                observed_arrival_time TEXT NOT NULL,
                source_system TEXT NOT NULL,
                feed_scope TEXT NOT NULL,
                operator_id TEXT,
                snapshot_label TEXT NOT NULL,
                ingested_at TIMESTAMPTZ NOT NULL
            ) ON COMMIT DROP;
            """
        )
        cursor.execute(f"TRUNCATE TABLE {ARCHIVE_STAGE_TABLE};")


def load_historic_stop_observations_archive(
    *,
    metadata_path: Path,
    truncate: bool = True,
    max_rows: int | None = None,
    insert_batch_size: int = DEFAULT_INSERT_BATCH_SIZE,
    local_timezone: str = DEFAULT_LOCAL_TIMEZONE,
) -> HistoricStopObservationsArchiveLoadResult:
    if max_rows is not None and max_rows <= 0:
        raise ValueError("max_rows must be positive when provided.")
    if insert_batch_size <= 0:
        raise ValueError("insert_batch_size must be positive.")

    acquisition_metadata = load_historic_archive_metadata(metadata_path)
    artifact_path = resolve_archive_artifact_path(metadata_path, acquisition_metadata)
    snapshot_label = build_archive_snapshot_label(acquisition_metadata)

    settings = get_postgres_settings()
    ensure_db_service()
    wait_for_database(settings)
    execute_sql_file(settings, DDL_FILE)
    if truncate:
        truncate_stop_observations(settings)

    load_metadata = {
        "source_system": str(acquisition_metadata["source_system"]),
        "feed_scope": str(acquisition_metadata["feed_scope"]),
        "operator_id": str(acquisition_metadata.get("operator_id") or ""),
        "snapshot_label": snapshot_label,
        "ingested_at": datetime.now(tz=UTC).isoformat(),
    }

    inserted_row_count = 0
    skipped_missing_required_count = 0
    batch: list[tuple[str, ...]] = []
    connection_url = build_postgres_connection_url()
    with psycopg.connect(connection_url) as connection:
        _ensure_archive_stage_table(connection)
        with zipfile.ZipFile(artifact_path, mode="r") as archive:
            with archive.open(STOP_OBSERVATIONS_FILENAME, mode="r") as raw_handle:
                text_handle = TextIOWrapper(raw_handle, encoding="utf-8", newline="")
                reader = csv.DictReader(text_handle)
                _validate_archive_headers(reader.fieldnames)

                for raw_row in reader:
                    transformed_row = _transform_archive_row(
                        raw_row,
                        load_metadata,
                        local_timezone=local_timezone,
                    )
                    if transformed_row is None:
                        skipped_missing_required_count += 1
                        continue

                    batch.append(transformed_row)
                    if max_rows is not None and (inserted_row_count + len(batch)) >= max_rows:
                        batch = batch[: max_rows - inserted_row_count]

                    if len(batch) >= insert_batch_size or (
                        max_rows is not None
                        and (inserted_row_count + len(batch)) >= max_rows
                    ):
                        inserted_row_count += _copy_archive_rows(
                            connection,
                            batch,
                            local_timezone=local_timezone,
                        )
                        batch = []

                    if max_rows is not None and inserted_row_count >= max_rows:
                        break

        if batch:
            inserted_row_count += _copy_archive_rows(
                connection,
                batch,
                local_timezone=local_timezone,
            )

    return HistoricStopObservationsArchiveLoadResult(
        inserted_row_count=inserted_row_count,
        skipped_missing_required_count=skipped_missing_required_count,
        snapshot_label=snapshot_label,
        metadata_path=metadata_path,
        artifact_path=artifact_path,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--metadata-path",
        type=Path,
        required=True,
        help="Path to the historic acquisition JSON sidecar created by the S06a fetch step.",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=None,
        help="Optional cap for inserted observation rows from the archive.",
    )
    parser.add_argument(
        "--insert-batch-size",
        type=int,
        default=DEFAULT_INSERT_BATCH_SIZE,
        help="Batch size used for raw.stop_observations inserts.",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to raw.stop_observations instead of truncating it first.",
    )
    args = parser.parse_args()

    result = load_historic_stop_observations_archive(
        metadata_path=args.metadata_path,
        truncate=not args.append,
        max_rows=args.max_rows,
        insert_batch_size=args.insert_batch_size,
    )

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "table_name",
            "inserted_row_count",
            "skipped_missing_required_count",
            "snapshot_label",
        ]
    )
    writer.writerow(
        [
            TABLE_NAME,
            result.inserted_row_count,
            result.skipped_missing_required_count,
            result.snapshot_label,
        ]
    )
    print(output.getvalue().strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
