"""Integration tests for the B3a stop wait metrics bundle."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


def _configure_src_paths() -> None:
    root = Path(__file__).resolve().parents[2]
    src_dir = root / "pipeline" / "src"
    src_str = str(src_dir)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)


_configure_src_paths()

from muni_lta_pipeline.canonical_observed_stop_events import (  # noqa: E402
    materialize_canonical_observed_stop_events,
)
from muni_lta_pipeline.canonical_scheduled_models import (  # noqa: E402
    materialize_canonical_scheduled_models,
)
from muni_lta_pipeline.gtfs_static_fixture_ingest import (  # noqa: E402
    get_postgres_settings,
    load_gtfs_static_fixture,
    run_psql_sql,
)
from muni_lta_pipeline.historic_stop_observations_fixture_ingest import (  # noqa: E402
    load_historic_stop_observations_fixture,
)
from muni_lta_pipeline.stop_wait_metrics import (  # noqa: E402
    materialize_stop_wait_metrics,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
GTFS_FIXTURE_DIR = REPO_ROOT / "fixtures" / "gtfs_static" / "metrics_core"
OBSERVATION_FIXTURE_DIR = (
    REPO_ROOT / "fixtures" / "stop_observations" / "regional_rg_metrics_core"
)


class StopWaitMetricsBundleIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        load_gtfs_static_fixture(
            fixture_dir=GTFS_FIXTURE_DIR,
            snapshot_label="fixture_metrics_core_v1",
        )
        materialize_canonical_scheduled_models()
        load_historic_stop_observations_fixture(
            fixture_dir=OBSERVATION_FIXTURE_DIR,
            snapshot_label="historic_2026_05_so_metrics_core_v1",
        )
        materialize_canonical_observed_stop_events()
        materialize_stop_wait_metrics()
        cls.settings = get_postgres_settings()

    def test_stop_wait_hotspots_are_queryable_with_stop_geometry_and_separate_from_segments(self) -> None:
        hotspot_rows = run_psql_sql(
            self.settings,
            """
            SELECT
                route_id,
                direction_id::TEXT,
                stop_id,
                stop_wait_label,
                stop_wait_strategy,
                ROUND(scheduled_effective_wait_minutes, 6)::TEXT,
                ROUND(observed_effective_wait_minutes, 6)::TEXT,
                ROUND(waiting_loss_minutes, 6)::TEXT,
                matched_headway_interval_count::TEXT,
                ST_SRID(geom)::TEXT,
                ST_IsValid(geom)::TEXT
            FROM serving.stop_wait_hotspots
            WHERE route_id = '14'
            ORDER BY direction_id, stop_id;
            """,
        ).splitlines()

        self.assertEqual(
            hotspot_rows,
            [
                "14|0|STP_24TH|24th St Mission (Downtown)|first_stop_exact_match|6.500000|6.653846|0.153846|2|4326|true",
                "14|1|STP_8TH|8th St Market (Outbound)|first_stop_exact_match|6.000000|7.500000|1.500000|2|4326|true",
            ],
        )

        route_summary = run_psql_sql(
            self.settings,
            """
            SELECT
                route_id,
                ROUND(waiting_loss_minutes, 6)::TEXT,
                worst_stop_wait_label,
                worst_segment_label
            FROM marts.route_window_summary
            WHERE route_id = '14';
            """,
        )

        self.assertEqual(
            route_summary,
            "14|0.829804|8th St Market (Outbound)|16th St Mission -> 24th St Mission",
        )

        direction_rows = run_psql_sql(
            self.settings,
            """
            SELECT
                route_id,
                direction_id::TEXT,
                worst_stop_wait_label,
                worst_segment_label
            FROM marts.route_direction_summary
            WHERE route_id = '14'
            ORDER BY direction_id;
            """,
        ).splitlines()

        self.assertEqual(
            direction_rows,
            [
                "14|0|24th St Mission (Downtown)|16th St Mission -> 8th St Market",
                "14|1|8th St Market (Outbound)|16th St Mission -> 24th St Mission",
            ],
        )

        route_map_row = run_psql_sql(
            self.settings,
            """
            SELECT
                route_id,
                worst_stop_wait_label,
                worst_segment_label,
                ST_SRID(geom)::TEXT,
                ST_IsValid(geom)::TEXT
            FROM serving.route_map_layer
            WHERE route_id = '14';
            """,
        )

        self.assertEqual(
            route_map_row,
            "14|8th St Market (Outbound)|16th St Mission -> 24th St Mission|4326|true",
        )


if __name__ == "__main__":
    unittest.main()
