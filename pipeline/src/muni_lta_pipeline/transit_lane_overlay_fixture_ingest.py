"""Load a small transit-only-lane GeoJSON fixture into raw Postgres for B3."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path

from muni_lta_pipeline.config import get_pipeline_settings
from muni_lta_pipeline.gtfs_static_fixture_ingest import (
    ensure_db_service,
    execute_sql_file,
    get_postgres_settings,
    run_psql_sql,
    sql_literal,
    wait_for_database,
)


DDL_FILE = (
    get_pipeline_settings().app_root
    / "db"
    / "sql"
    / "06-create-raw-transit-lane-overlays-table.sql"
)
RAW_TABLE_NAME = "raw.transit_only_lanes"
TABLE_COLUMNS = (
    "overlay_id",
    "street_name",
    "segment_name",
    "route_hint",
    "geom_geojson",
)
METADATA_COLUMNS = (
    "source_system",
    "feed_scope",
    "operator_id",
    "snapshot_label",
    "ingested_at",
)


def get_default_fixture_path() -> Path:
    return (
        get_pipeline_settings().fixtures_root
        / "geospatial"
        / "transit_only_lanes"
        / "minimal.geojson"
    )


DEFAULT_FIXTURE_PATH = get_default_fixture_path()


def read_fixture_rows(fixture_path: Path, metadata: dict[str, str]) -> list[dict[str, str]]:
    if not fixture_path.exists():
        raise FileNotFoundError(f"Missing transit-lane fixture: {fixture_path}")

    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    if payload.get("type") != "FeatureCollection":
        raise ValueError(f"Fixture {fixture_path} must be a GeoJSON FeatureCollection.")

    rows: list[dict[str, str]] = []
    for index, feature in enumerate(payload.get("features", []), start=1):
        properties = feature.get("properties") or {}
        geometry = feature.get("geometry")
        if not geometry:
            raise ValueError(f"Feature {index} in {fixture_path} is missing geometry.")

        row = {
            "overlay_id": str(properties.get("overlay_id") or f"overlay_{index}"),
            "street_name": str(properties.get("street_name") or "").strip(),
            "segment_name": str(properties.get("segment_name") or "").strip(),
            "route_hint": str(properties.get("route_hint") or "").strip(),
            "geom_geojson": json.dumps(geometry, separators=(",", ":")),
            **metadata,
        }

        missing = [column for column in ("street_name", "segment_name") if not row[column]]
        if missing:
            raise ValueError(
                f"Feature {index} in {fixture_path} is missing required properties: {', '.join(missing)}"
            )

        rows.append(row)

    return rows


def truncate_overlay_table(settings) -> None:
    run_psql_sql(settings, f"TRUNCATE TABLE {RAW_TABLE_NAME};")


def insert_rows(settings, rows: list[dict[str, str]]) -> int:
    if not rows:
        return 0

    columns = [*TABLE_COLUMNS, *METADATA_COLUMNS]
    values_sql: list[str] = []
    for row in rows:
        values = ", ".join(sql_literal(row[column]) for column in columns)
        values_sql.append(f"({values})")

    run_psql_sql(
        settings,
        f"INSERT INTO {RAW_TABLE_NAME} ({', '.join(columns)}) VALUES\n" + ",\n".join(values_sql) + ";",
    )
    return len(rows)


def load_transit_lane_overlay_fixture(
    *,
    fixture_path: Path | None = None,
    source_system: str = "sfmta_open_data",
    feed_scope: str = "context_overlay",
    operator_id: str = "SFMTA",
    snapshot_label: str = "fixture_transit_lanes_v1",
) -> int:
    fixture_path = fixture_path or get_default_fixture_path()
    settings = get_postgres_settings()
    ensure_db_service()
    wait_for_database(settings)
    execute_sql_file(settings, DDL_FILE)
    truncate_overlay_table(settings)

    metadata = {
        "source_system": source_system,
        "feed_scope": feed_scope,
        "operator_id": operator_id,
        "snapshot_label": snapshot_label,
        "ingested_at": datetime.now(tz=UTC).isoformat(),
    }
    rows = read_fixture_rows(fixture_path, metadata)
    return insert_rows(settings, rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixture-path",
        type=Path,
        default=get_default_fixture_path(),
        help="Path to the transit-only-lane GeoJSON fixture.",
    )
    parser.add_argument(
        "--snapshot-label",
        default="fixture_transit_lanes_v1",
        help="Snapshot label stored in raw ingest metadata.",
    )
    args = parser.parse_args()

    row_count = load_transit_lane_overlay_fixture(
        fixture_path=args.fixture_path,
        snapshot_label=args.snapshot_label,
    )

    output = StringIO()
    output.write("table_name,row_count\n")
    output.write(f"{RAW_TABLE_NAME},{row_count}")
    print(output.getvalue())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
