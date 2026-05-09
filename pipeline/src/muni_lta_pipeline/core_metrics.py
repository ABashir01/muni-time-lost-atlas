"""Materialize the dbt route-summary marts for the first rider-time-loss graph."""

from __future__ import annotations

import argparse
from pathlib import Path

from muni_lta_pipeline.dbt_runner import run_dbt_build
from muni_lta_pipeline.gtfs_static_fixture_ingest import DEFAULT_FIXTURE_DIR


def materialize_core_metrics() -> None:
    run_dbt_build(
        [
            "path:models/staging/gtfs",
            "path:models/staging/observations",
            "path:models/canonical/scheduled",
            "path:models/canonical/observed",
            "path:models/canonical/spatial",
            "path:models/marts/core_metrics",
            "path:models/marts/segment_metrics",
        ],
        excludes=[
            "path:models/staging/geospatial",
            "path:models/serving",
        ],
    )


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
