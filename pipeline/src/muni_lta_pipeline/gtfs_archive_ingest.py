"""Load fetched 511 GTFS zip artifacts into raw.gtfs_* tables."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import UTC, datetime
from io import StringIO, TextIOWrapper
import json
import os
from pathlib import Path
from typing import Any, Mapping
import zipfile

import psycopg

from muni_lta_pipeline.gtfs_static_fixture_ingest import (
    DDL_FILE,
    METADATA_COLUMNS,
    RAW_GTFS_TABLES,
    REPO_ROOT,
    RawGtfsTable,
    build_postgres_connection_url,
    ensure_db_service,
    execute_sql_file,
    get_postgres_settings,
    run_psql_sql,
    truncate_raw_gtfs_tables,
    wait_for_database,
)


OPTIONAL_GTFS_FILES = {"calendar.txt", "calendar_dates.txt"}


@dataclass(frozen=True)
class GtfsArchiveLoadResult:
    artifact_path: Path
    metadata_path: Path
    snapshot_label: str
    feed_scope: str
    operator_id: str
    inserted_row_counts: dict[str, int]


def load_gtfs_acquisition_metadata(metadata_path: Path) -> dict[str, Any]:
    if not metadata_path.exists():
        raise FileNotFoundError(f"GTFS acquisition metadata file not found: {metadata_path}")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    required_fields = (
        "source_system",
        "feed_scope",
        "artifact_filename",
    )
    missing_fields = [field for field in required_fields if field not in metadata]
    if missing_fields:
        raise ValueError(
            "GTFS acquisition metadata is missing required fields: "
            + ", ".join(missing_fields)
        )

    return metadata


def resolve_archive_artifact_path(metadata_path: Path, metadata: Mapping[str, Any]) -> Path:
    artifact_filename = str(metadata["artifact_filename"]).strip()
    if not artifact_filename:
        raise ValueError("GTFS acquisition metadata must include artifact_filename.")

    artifact_path = metadata_path.parent / artifact_filename
    if not artifact_path.exists():
        raise FileNotFoundError(f"GTFS archive zip not found: {artifact_path}")
    return artifact_path


def build_archive_snapshot_label(metadata: Mapping[str, Any]) -> str:
    artifact_stem = Path(str(metadata["artifact_filename"])).stem
    return f"archive_{artifact_stem}"


def raw_gtfs_tables_exist() -> bool:
    settings = get_postgres_settings(os.environ)
    table_count = int(
        run_psql_sql(
            settings,
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'raw'
              AND table_name IN (
                  'gtfs_routes',
                  'gtfs_trips',
                  'gtfs_stops',
                  'gtfs_stop_times',
                  'gtfs_shapes',
                  'gtfs_calendar',
                  'gtfs_calendar_dates'
              );
            """,
        )
    )
    return table_count == len(RAW_GTFS_TABLES)


def _validate_archive_headers(
    fieldnames: list[str] | None,
    table: RawGtfsTable,
) -> None:
    if fieldnames is None:
        raise ValueError(f"{table.source_file} has no header row in the GTFS archive.")

    missing_headers = [column for column in table.table_columns if column not in fieldnames]
    if missing_headers:
        raise ValueError(
            f"{table.source_file} is missing required columns: {', '.join(missing_headers)}"
        )


def _copy_archive_table(
    connection: psycopg.Connection[Any],
    archive: zipfile.ZipFile,
    table: RawGtfsTable,
    metadata: Mapping[str, str],
) -> int:
    if table.source_file not in archive.namelist():
        if table.source_file in OPTIONAL_GTFS_FILES:
            return 0
        raise FileNotFoundError(
            f"Required GTFS file {table.source_file} is missing from the archive."
        )

    columns = [*table.table_columns, *METADATA_COLUMNS]
    copy_sql = (
        f"COPY {table.table_name} ({', '.join(columns)}) FROM STDIN"
    )
    inserted_row_count = 0

    with archive.open(table.source_file, mode="r") as raw_handle:
        reader = csv.DictReader(TextIOWrapper(raw_handle, encoding="utf-8", newline=""))
        _validate_archive_headers(reader.fieldnames, table)

        with connection.cursor() as cursor:
            with cursor.copy(copy_sql) as copy:
                for raw_row in reader:
                    row_values = [
                        (raw_row.get(column) or "").strip() for column in table.table_columns
                    ]
                    metadata_values = [metadata[column] for column in METADATA_COLUMNS]
                    copy.write_row([*row_values, *metadata_values])
                    inserted_row_count += 1

    return inserted_row_count


def load_gtfs_archive(
    *,
    metadata_path: Path,
    truncate: bool = True,
) -> GtfsArchiveLoadResult:
    settings = get_postgres_settings(os.environ)
    ensure_db_service()
    wait_for_database(settings)
    if truncate or not raw_gtfs_tables_exist():
        execute_sql_file(settings, DDL_FILE)
    if truncate:
        truncate_raw_gtfs_tables(settings)

    acquisition_metadata = load_gtfs_acquisition_metadata(metadata_path)
    artifact_path = resolve_archive_artifact_path(metadata_path, acquisition_metadata)
    snapshot_label = build_archive_snapshot_label(acquisition_metadata)
    load_metadata = {
        "source_system": str(acquisition_metadata["source_system"]),
        "feed_scope": str(acquisition_metadata["feed_scope"]),
        "operator_id": str(acquisition_metadata.get("operator_id") or ""),
        "snapshot_label": snapshot_label,
        "ingested_at": datetime.now(tz=UTC).isoformat(),
    }

    inserted_row_counts: dict[str, int] = {}
    connection_url = build_postgres_connection_url(os.environ)
    with psycopg.connect(connection_url) as connection:
        with zipfile.ZipFile(artifact_path, mode="r") as archive:
            for table in RAW_GTFS_TABLES:
                inserted_row_counts[table.table_name] = _copy_archive_table(
                    connection,
                    archive,
                    table,
                    load_metadata,
                )

    return GtfsArchiveLoadResult(
        artifact_path=artifact_path,
        metadata_path=metadata_path,
        snapshot_label=snapshot_label,
        feed_scope=str(acquisition_metadata["feed_scope"]),
        operator_id=str(acquisition_metadata.get("operator_id") or ""),
        inserted_row_counts=inserted_row_counts,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--metadata-path",
        type=Path,
        required=True,
        help="Path to the acquisition JSON sidecar created by a 511 GTFS fetch step.",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append this GTFS archive snapshot instead of truncating raw.gtfs_* first.",
    )
    args = parser.parse_args()

    result = load_gtfs_archive(
        metadata_path=args.metadata_path,
        truncate=not args.append,
    )

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["table_name", "row_count", "snapshot_label"])
    for table_name, row_count in result.inserted_row_counts.items():
        writer.writerow([table_name, row_count, result.snapshot_label])
    print(output.getvalue().strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
