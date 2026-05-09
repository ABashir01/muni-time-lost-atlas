"""Materialize the dbt observed stop-event graph on top of the scheduled models."""

from __future__ import annotations

import argparse
from pathlib import Path

from muni_lta_pipeline.dbt_runner import run_dbt_build
from muni_lta_pipeline.gtfs_static_fixture_ingest import DEFAULT_FIXTURE_DIR


def materialize_canonical_observed_stop_events() -> None:
    run_dbt_build(
        [
            "path:models/staging/gtfs",
            "path:models/staging/observations",
            "path:models/canonical/scheduled",
            "path:models/canonical/observed",
        ],
        excludes=["path:models/marts"],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixture-dir",
        type=Path,
        default=DEFAULT_FIXTURE_DIR,
        help="Unused in S07; kept for interface symmetry with earlier pipeline entrypoints.",
    )
    parser.parse_args()
    materialize_canonical_observed_stop_events()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
