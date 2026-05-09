"""Integration tests for the B1 core metrics bundle."""

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
from muni_lta_pipeline.core_metrics import materialize_core_metrics  # noqa: E402
from muni_lta_pipeline.gtfs_static_fixture_ingest import (  # noqa: E402
    get_postgres_settings,
    load_gtfs_static_fixture,
    run_psql_sql,
)
from muni_lta_pipeline.historic_stop_observations_fixture_ingest import (  # noqa: E402
    load_historic_stop_observations_fixture,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
GTFS_FIXTURE_DIR = REPO_ROOT / "fixtures" / "gtfs_static" / "metrics_core"
OBSERVATION_FIXTURE_DIR = (
    REPO_ROOT / "fixtures" / "stop_observations" / "regional_rg_metrics_core"
)


class CoreMetricsBundleIntegrationTests(unittest.TestCase):
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
        materialize_core_metrics()
        cls.settings = get_postgres_settings()

    def test_route_window_summary_matches_controlled_waiting_and_runtime_math(self) -> None:
        row = run_psql_sql(
            self.settings,
            """
            SELECT
                route_id,
                window_key,
                ROUND(typical_trip_loss_minutes, 6)::TEXT,
                ROUND(waiting_loss_minutes, 6)::TEXT,
                ROUND(in_vehicle_loss_minutes, 6)::TEXT,
                matched_observed_stop_event_count::TEXT,
                resolved_unmatched_observation_count::TEXT,
                matched_headway_interval_count::TEXT,
                matched_full_trip_count::TEXT
            FROM marts.route_window_summary
            WHERE route_id = '14';
            """,
        )

        self.assertEqual(
            row,
            "14|all_day|2.329804|0.829804|1.500000|18|1|4|6",
        )

    def test_route_direction_summary_keeps_direction_level_metrics_and_unmatched_counts_separate(self) -> None:
        rows = run_psql_sql(
            self.settings,
            """
            SELECT
                route_id,
                direction_id::TEXT,
                direction_label,
                ROUND(typical_trip_loss_minutes, 6)::TEXT,
                ROUND(waiting_loss_minutes, 6)::TEXT,
                ROUND(in_vehicle_loss_minutes, 6)::TEXT,
                matched_observed_stop_event_count::TEXT,
                resolved_unmatched_observation_count::TEXT,
                matched_headway_interval_count::TEXT,
                matched_full_trip_count::TEXT
            FROM marts.route_direction_summary
            WHERE route_id = '14'
            ORDER BY direction_id;
            """,
        ).splitlines()

        self.assertEqual(
            rows,
            [
                "14|0|Downtown|1.153846|0.153846|1.000000|9|1|2|3",
                "14|1|Outbound|3.500000|1.500000|2.000000|9|0|2|3",
            ],
        )

    def test_route_hour_summary_is_queryable_by_direction_and_hour(self) -> None:
        rows = run_psql_sql(
            self.settings,
            """
            SELECT
                route_id,
                direction_id::TEXT,
                hour_local::TEXT,
                ROUND(typical_trip_loss_minutes, 6)::TEXT,
                ROUND(waiting_loss_minutes, 6)::TEXT,
                ROUND(in_vehicle_loss_minutes, 6)::TEXT,
                matched_observed_stop_event_count::TEXT,
                resolved_unmatched_observation_count::TEXT
            FROM marts.route_hour_summary
            WHERE route_id = '14'
            ORDER BY direction_id, hour_local;
            """,
        ).splitlines()

        self.assertEqual(
            rows,
            [
                "14|0|8|1.153846|0.153846|1.000000|9|1",
                "14|1|9|3.500000|1.500000|2.000000|9|0",
            ],
        )

    def test_unmatched_rows_remain_outside_metric_numerators(self) -> None:
        summary_rows = run_psql_sql(
            self.settings,
            """
            SELECT join_status, row_count
            FROM canonical.observed_stop_event_join_summary
            WHERE observed_snapshot_label = 'historic_2026_05_so_metrics_core_v1'
            ORDER BY join_status;
            """,
        ).splitlines()

        self.assertEqual(
            summary_rows,
            [
                "matched_exact|18",
                "unmatched_stop_id|1",
                "unmatched_trip_service_date|1",
            ],
        )

        metric_rows = int(
            run_psql_sql(
                self.settings,
                """
                SELECT COUNT(*)
                FROM canonical.observed_stop_events
                WHERE observed_snapshot_label = 'historic_2026_05_so_metrics_core_v1';
                """,
            )
        )
        self.assertEqual(metric_rows, 18)


if __name__ == "__main__":
    unittest.main()
