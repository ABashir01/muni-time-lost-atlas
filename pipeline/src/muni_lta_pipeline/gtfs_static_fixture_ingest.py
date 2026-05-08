"""Load a tiny GTFS static fixture into raw Postgres tables for slice S04."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import UTC, datetime
from io import StringIO
import os
from pathlib import Path
import subprocess
import time
from typing import Iterable, Mapping


REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = REPO_ROOT / ".env"
DDL_FILE = REPO_ROOT / "db" / "sql" / "01-create-raw-gtfs-tables.sql"
DEFAULT_FIXTURE_DIR = REPO_ROOT / "fixtures" / "gtfs_static" / "minimal"


@dataclass(frozen=True)
class PostgresSettings:
    database: str
    user: str
    password: str


@dataclass(frozen=True)
class RawGtfsTable:
    source_file: str
    table_name: str
    table_columns: tuple[str, ...]


RAW_GTFS_TABLES: tuple[RawGtfsTable, ...] = (
    RawGtfsTable(
        source_file="routes.txt",
        table_name="raw.gtfs_routes",
        table_columns=(
            "route_id",
            "agency_id",
            "route_short_name",
            "route_long_name",
            "route_type",
            "route_color",
            "route_text_color",
        ),
    ),
    RawGtfsTable(
        source_file="trips.txt",
        table_name="raw.gtfs_trips",
        table_columns=(
            "route_id",
            "service_id",
            "trip_id",
            "trip_headsign",
            "direction_id",
            "shape_id",
        ),
    ),
    RawGtfsTable(
        source_file="stops.txt",
        table_name="raw.gtfs_stops",
        table_columns=("stop_id", "stop_name", "stop_lat", "stop_lon"),
    ),
    RawGtfsTable(
        source_file="stop_times.txt",
        table_name="raw.gtfs_stop_times",
        table_columns=(
            "trip_id",
            "arrival_time",
            "departure_time",
            "stop_id",
            "stop_sequence",
            "shape_dist_traveled",
        ),
    ),
    RawGtfsTable(
        source_file="shapes.txt",
        table_name="raw.gtfs_shapes",
        table_columns=(
            "shape_id",
            "shape_pt_lat",
            "shape_pt_lon",
            "shape_pt_sequence",
            "shape_dist_traveled",
        ),
    ),
    RawGtfsTable(
        source_file="calendar.txt",
        table_name="raw.gtfs_calendar",
        table_columns=(
            "service_id",
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
            "start_date",
            "end_date",
        ),
    ),
    RawGtfsTable(
        source_file="calendar_dates.txt",
        table_name="raw.gtfs_calendar_dates",
        table_columns=("service_id", "date", "exception_type"),
    ),
)

METADATA_COLUMNS = (
    "source_system",
    "feed_scope",
    "operator_id",
    "snapshot_label",
    "ingested_at",
)

TRUNCATE_ORDER = (
    "raw.gtfs_stop_times",
    "raw.gtfs_shapes",
    "raw.gtfs_trips",
    "raw.gtfs_stops",
    "raw.gtfs_routes",
    "raw.gtfs_calendar_dates",
    "raw.gtfs_calendar",
)


def load_env_file(path: Path = ENV_FILE) -> dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(
            "Missing .env at repo root. Copy .env.example to .env and set local DB values."
        )

    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()

    return values


def get_postgres_settings(environ: Mapping[str, str] | None = None) -> PostgresSettings:
    env = dict(load_env_file())
    if environ:
        env.update(environ)

    return PostgresSettings(
        database=env["POSTGRES_DB"],
        user=env["POSTGRES_USER"],
        password=env["POSTGRES_PASSWORD"],
    )


def run_command(
    command: list[str],
    *,
    input_text: str | None = None,
    capture_output: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        input=input_text,
        text=True,
        capture_output=capture_output,
        check=False,
    )
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        stdout = (result.stdout or "").strip()
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(command)}\nSTDOUT: {stdout}\nSTDERR: {stderr}"
        )
    return result


def docker_compose_psql_args(settings: PostgresSettings) -> list[str]:
    return [
        "docker",
        "compose",
        "exec",
        "-T",
        "-e",
        f"PGPASSWORD={settings.password}",
        "db",
        "psql",
        "-v",
        "ON_ERROR_STOP=1",
        "-h",
        "127.0.0.1",
        "-U",
        settings.user,
        "-d",
        settings.database,
    ]


def ensure_db_service() -> None:
    run_command(["docker", "compose", "up", "-d", "db"])


def wait_for_database(settings: PostgresSettings, attempts: int = 12, sleep_seconds: int = 2) -> None:
    for _ in range(attempts):
        try:
            run_psql_sql(settings, "SELECT 1;")
            return
        except RuntimeError:
            time.sleep(sleep_seconds)
    raise RuntimeError("The Postgres service did not become ready in time.")


def run_psql_sql(settings: PostgresSettings, sql: str) -> str:
    result = run_command(
        [*docker_compose_psql_args(settings), "-t", "-A", "-c", sql]
    )
    return result.stdout.strip()


def execute_sql_file(settings: PostgresSettings, path: Path) -> None:
    run_psql_sql(settings, path.read_text(encoding="utf-8"))


def sql_literal(value: str) -> str:
    escaped = value.replace("'", "''")
    return f"'{escaped}'"


def read_fixture_rows(
    table: RawGtfsTable,
    fixture_dir: Path,
    metadata: Mapping[str, str],
) -> list[dict[str, str]]:
    file_path = fixture_dir / table.source_file
    if not file_path.exists():
        raise FileNotFoundError(f"Missing GTFS fixture file: {file_path}")

    with file_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"Fixture file {file_path} has no header row.")

        missing_headers = [col for col in table.table_columns if col not in reader.fieldnames]
        if missing_headers:
            raise ValueError(
                f"Fixture file {file_path} is missing required columns: {', '.join(missing_headers)}"
            )

        rows: list[dict[str, str]] = []
        for raw_row in reader:
            row: dict[str, str] = {}
            for column in table.table_columns:
                row[column] = raw_row.get(column, "")
            row.update(metadata)
            rows.append(row)

    return rows


def truncate_raw_gtfs_tables(settings: PostgresSettings) -> None:
    joined_tables = ", ".join(TRUNCATE_ORDER)
    run_psql_sql(settings, f"TRUNCATE TABLE {joined_tables};")


def insert_rows(settings: PostgresSettings, table: RawGtfsTable, rows: Iterable[Mapping[str, str]]) -> int:
    row_list = list(rows)
    if not row_list:
        return 0

    columns = [*table.table_columns, *METADATA_COLUMNS]
    values_sql: list[str] = []
    for row in row_list:
        values = ", ".join(sql_literal(row[column]) for column in columns)
        values_sql.append(f"({values})")

    insert_sql = (
        f"INSERT INTO {table.table_name} ({', '.join(columns)}) VALUES\n"
        + ",\n".join(values_sql)
        + ";"
    )
    run_psql_sql(settings, insert_sql)
    return len(row_list)


def load_gtfs_static_fixture(
    *,
    fixture_dir: Path = DEFAULT_FIXTURE_DIR,
    source_system: str = "511",
    feed_scope: str = "operator_active",
    operator_id: str = "SF",
    snapshot_label: str = "fixture_minimal_v1",
) -> dict[str, int]:
    settings = get_postgres_settings(os.environ)
    ensure_db_service()
    wait_for_database(settings)
    execute_sql_file(settings, DDL_FILE)
    truncate_raw_gtfs_tables(settings)

    metadata = {
        "source_system": source_system,
        "feed_scope": feed_scope,
        "operator_id": operator_id,
        "snapshot_label": snapshot_label,
        "ingested_at": datetime.now(tz=UTC).isoformat(),
    }

    counts: dict[str, int] = {}
    for table in RAW_GTFS_TABLES:
        rows = read_fixture_rows(table, fixture_dir, metadata)
        counts[table.table_name] = insert_rows(settings, table, rows)

    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixture-dir",
        type=Path,
        default=DEFAULT_FIXTURE_DIR,
        help="Path to the GTFS static fixture directory.",
    )
    parser.add_argument(
        "--snapshot-label",
        default="fixture_minimal_v1",
        help="Snapshot label stored in raw ingest metadata.",
    )
    args = parser.parse_args()

    counts = load_gtfs_static_fixture(
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
