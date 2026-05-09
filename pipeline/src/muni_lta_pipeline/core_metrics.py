"""Materialize the first rider-time-loss marts for bundle B1."""

from __future__ import annotations

import argparse
from pathlib import Path

from muni_lta_pipeline.gtfs_static_fixture_ingest import (
    DEFAULT_FIXTURE_DIR,
    ensure_db_service,
    execute_sql_file,
    get_postgres_settings,
    wait_for_database,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
MATERIALIZATION_SQL = REPO_ROOT / "db" / "sql" / "05-materialize-core-metrics.sql"


def materialize_core_metrics() -> None:
    settings = get_postgres_settings()
    ensure_db_service()
    wait_for_database(settings)
    execute_sql_file(settings, MATERIALIZATION_SQL)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixture-dir",
        type=Path,
        default=DEFAULT_FIXTURE_DIR,
        help="Unused in B1; kept for interface symmetry with earlier pipeline entrypoints.",
    )
    parser.parse_args()
    materialize_core_metrics()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
