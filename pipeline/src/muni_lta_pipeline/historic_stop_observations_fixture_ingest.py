"""Load a tiny historic stop_observations fixture into the raw Postgres table for slice S06."""

from __future__ import annotations

import argparse
import csv
from datetime import UTC, date, datetime
from io import StringIO
from pathlib import Path
import re
from typing import Iterable, Mapping

from muni_lta_pipeline.gtfs_static_fixture_ingest import (
    ensure_db_service,
    execute_sql_file,
    get_postgres_settings,
    run_psql_sql,
    sql_literal,
    wait_for_database,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DDL_FILE = REPO_ROOT / "db" / "sql" / "03-create-raw-stop-observations-table.sql"
DEFAULT_FIXTURE_DIR = REPO_ROOT / "fixtures" / "stop_observations" / "regional_rg_minimal"
FIXTURE_FILENAME = "stop_observations.txt"
TABLE_NAME = "raw.stop_observations"
TABLE_COLUMNS = (
    "service_date",
    "trip_id",
    "stop_id",
    "stop_sequence",
    "observed_arrival_time",
    "observed_arrival_ts",
)
METADATA_COLUMNS = (
    "source_system",
    "feed_scope",
    "operator_id",
    "snapshot_label",
    "ingested_at",
)
REQUIRED_FIXTURE_COLUMNS = TABLE_COLUMNS[:-1]
SERVICE_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_service_date(value: str) -> date:
    if not SERVICE_DATE_PATTERN.fullmatch(value):
        raise ValueError(
            f"service_date must be YYYY-MM-DD; received {value!r}."
        )
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"service_date must be YYYY-MM-DD; received {value!r}."
        ) from exc


def parse_observed_arrival_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(
            "observed_arrival_time must be an ISO-8601 timestamp with timezone offset."
        ) from exc

    if parsed.tzinfo is None:
        raise ValueError(
            "observed_arrival_time must include a timezone offset."
        )

    return parsed


def truncate_stop_observations(settings: object) -> None:
    run_psql_sql(settings, f"TRUNCATE TABLE {TABLE_NAME};")


def read_fixture_rows(
    fixture_dir: Path,
    metadata: Mapping[str, str],
) -> list[dict[str, str]]:
    file_path = fixture_dir / FIXTURE_FILENAME
    if not file_path.exists():
        raise FileNotFoundError(f"Missing stop observations fixture file: {file_path}")

    with file_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"Fixture file {file_path} has no header row.")

        missing_headers = [
            column for column in REQUIRED_FIXTURE_COLUMNS if column not in reader.fieldnames
        ]
        if missing_headers:
            raise ValueError(
                f"Fixture file {file_path} is missing required columns: {', '.join(missing_headers)}"
            )

        rows: list[dict[str, str]] = []
        for raw_row in reader:
            service_date_value = (raw_row.get("service_date") or "").strip()
            trip_id = (raw_row.get("trip_id") or "").strip()
            stop_id = (raw_row.get("stop_id") or "").strip()
            stop_sequence = (raw_row.get("stop_sequence") or "").strip()
            observed_arrival_time = (raw_row.get("observed_arrival_time") or "").strip()

            if not service_date_value or not trip_id or not stop_id or not stop_sequence or not observed_arrival_time:
                raise ValueError("Fixture rows must populate service_date, trip_id, stop_id, stop_sequence, and observed_arrival_time.")

            parsed_service_date = parse_service_date(service_date_value)
            parsed_observed_arrival = parse_observed_arrival_timestamp(observed_arrival_time)

            row = {
                "service_date": parsed_service_date.isoformat(),
                "trip_id": trip_id,
                "stop_id": stop_id,
                "stop_sequence": stop_sequence,
                "observed_arrival_time": observed_arrival_time,
                "observed_arrival_ts": parsed_observed_arrival.isoformat(),
            }
            row.update(metadata)
            rows.append(row)

    return rows


def insert_rows(settings: object, rows: Iterable[Mapping[str, str]]) -> int:
    row_list = list(rows)
    if not row_list:
        return 0

    columns = [*TABLE_COLUMNS, *METADATA_COLUMNS]
    values_sql: list[str] = []
    for row in row_list:
        values_sql.append(
            "(" + ", ".join(sql_literal(row[column]) for column in columns) + ")"
        )

    insert_sql = (
        f"INSERT INTO {TABLE_NAME} ({', '.join(columns)}) VALUES\n"
        + ",\n".join(values_sql)
        + ";"
    )
    run_psql_sql(settings, insert_sql)
    return len(row_list)


def load_historic_stop_observations_fixture(
    *,
    fixture_dir: Path = DEFAULT_FIXTURE_DIR,
    source_system: str = "511",
    feed_scope: str = "regional_historic",
    operator_id: str = "RG",
    snapshot_label: str = "historic_2026_05_so_fixture_v1",
) -> dict[str, int]:
    settings = get_postgres_settings()
    ensure_db_service()
    wait_for_database(settings)
    execute_sql_file(settings, DDL_FILE)
    truncate_stop_observations(settings)

    metadata = {
        "source_system": source_system,
        "feed_scope": feed_scope,
        "operator_id": operator_id,
        "snapshot_label": snapshot_label,
        "ingested_at": datetime.now(tz=UTC).isoformat(),
    }

    rows = read_fixture_rows(fixture_dir, metadata)
    inserted_count = insert_rows(settings, rows)
    return {TABLE_NAME: inserted_count}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixture-dir",
        type=Path,
        default=DEFAULT_FIXTURE_DIR,
        help="Path to the historic stop_observations fixture directory.",
    )
    parser.add_argument(
        "--snapshot-label",
        default="historic_2026_05_so_fixture_v1",
        help="Snapshot label stored in raw ingest metadata.",
    )
    args = parser.parse_args()

    counts = load_historic_stop_observations_fixture(
        fixture_dir=args.fixture_dir,
        snapshot_label=args.snapshot_label,
    )

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["table_name", "row_count"])
    for table_name, row_count in counts.items():
        writer.writerow([table_name, row_count])
    print(output.getvalue().strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
