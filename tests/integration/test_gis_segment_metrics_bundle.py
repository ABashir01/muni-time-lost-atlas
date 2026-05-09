"""Integration tests for the B3 GIS and segment metrics bundle."""

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
from muni_lta_pipeline.gis_segment_metrics import (  # noqa: E402
    materialize_gis_segment_metrics,
)
from muni_lta_pipeline.gtfs_static_fixture_ingest import (  # noqa: E402
    get_postgres_settings,
    load_gtfs_static_fixture,
    run_psql_sql,
)
from muni_lta_pipeline.historic_stop_observations_fixture_ingest import (  # noqa: E402
    load_historic_stop_observations_fixture,
)
from muni_lta_pipeline.transit_lane_overlay_fixture_ingest import (  # noqa: E402
    DEFAULT_FIXTURE_PATH as OVERLAY_FIXTURE_PATH,
    load_transit_lane_overlay_fixture,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
GTFS_FIXTURE_DIR = REPO_ROOT / "fixtures" / "gtfs_static" / "metrics_core"
OBSERVATION_FIXTURE_DIR = (
    REPO_ROOT / "fixtures" / "stop_observations" / "regional_rg_metrics_core"
)


class GisSegmentMetricsBundleIntegrationTests(unittest.TestCase):
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
        load_transit_lane_overlay_fixture(
            fixture_path=OVERLAY_FIXTURE_PATH,
            snapshot_label="fixture_transit_lanes_v1",
        )
        materialize_gis_segment_metrics()
        cls.settings = get_postgres_settings()

    def test_route_geometry_segment_metrics_and_overlay_are_queryable_together(self) -> None:
        route_row = run_psql_sql(
            self.settings,
            """
            SELECT
                route_id,
                ROUND(typical_trip_loss_minutes, 6)::TEXT,
                worst_segment_label,
                ST_SRID(geom)::TEXT,
                ST_IsValid(geom)::TEXT
            FROM serving.route_map_layer
            WHERE route_id = '14';
            """,
        )

        self.assertEqual(
            route_row,
            "14|2.329804|16th St Mission -> 24th St Mission|4326|true",
        )

        segment_rows = run_psql_sql(
            self.settings,
            """
            SELECT
                segment.direction_id::TEXT,
                segment.segment_sequence::TEXT,
                segment.segment_label,
                ROUND(segment.segment_in_vehicle_loss_minutes, 6)::TEXT,
                segment.matched_trip_segment_count::TEXT,
                ST_SRID(segment.geom)::TEXT,
                ST_IsValid(segment.geom)::TEXT
            FROM serving.route_segment_layer AS segment
            WHERE segment.route_id = '14'
            GROUP BY
                segment.direction_id,
                segment.segment_sequence,
                segment.segment_label,
                segment.segment_in_vehicle_loss_minutes,
                segment.matched_trip_segment_count,
                segment.geom
            ORDER BY segment.direction_id, segment.segment_sequence;
            """,
        ).splitlines()

        self.assertEqual(
            segment_rows,
            [
                "0|1|24th St Mission -> 16th St Mission|0.000000|3|4326|true",
                "0|2|16th St Mission -> 8th St Market|1.000000|3|4326|true",
                "1|1|8th St Market -> 16th St Mission|1.000000|3|4326|true",
                "1|2|16th St Mission -> 24th St Mission|2.000000|3|4326|true",
            ],
        )

        overlay_row = run_psql_sql(
            self.settings,
            """
            SELECT
                COUNT(*)::TEXT,
                MIN(ST_SRID(geom))::TEXT,
                BOOL_AND(ST_IsValid(geom))::TEXT,
                (
                    SELECT COUNT(DISTINCT CONCAT(segment.direction_id::TEXT, '-', segment.segment_sequence::TEXT))
                    FROM serving.route_segment_layer AS segment
                    JOIN serving.transit_only_lane_overlay AS overlay
                      ON ST_DWithin(segment.geom::geography, overlay.geom::geography, 25)
                    WHERE segment.route_id = '14'
                )::TEXT
            FROM serving.transit_only_lane_overlay;
            """,
        )

        self.assertEqual(overlay_row, "2|4326|true|4")

    def test_route_summaries_keep_prior_metric_math_and_add_worst_segment_labels(self) -> None:
        route_summary = run_psql_sql(
            self.settings,
            """
            SELECT
                route_id,
                window_key,
                ROUND(typical_trip_loss_minutes, 6)::TEXT,
                ROUND(waiting_loss_minutes, 6)::TEXT,
                ROUND(in_vehicle_loss_minutes, 6)::TEXT,
                worst_segment_label,
                matched_observed_stop_event_count::TEXT,
                resolved_unmatched_observation_count::TEXT,
                matched_headway_interval_count::TEXT,
                matched_full_trip_count::TEXT
            FROM marts.route_window_summary
            WHERE route_id = '14';
            """,
        )

        self.assertEqual(
            route_summary,
            "14|all_day|2.329804|0.829804|1.500000|16th St Mission -> 24th St Mission|18|1|4|6",
        )

        direction_rows = run_psql_sql(
            self.settings,
            """
            SELECT
                route_id,
                direction_id::TEXT,
                worst_segment_label
            FROM marts.route_direction_summary
            WHERE route_id = '14'
            ORDER BY direction_id;
            """,
        ).splitlines()

        self.assertEqual(
            direction_rows,
            [
                "14|0|16th St Mission -> 8th St Market",
                "14|1|16th St Mission -> 24th St Mission",
            ],
        )


if __name__ == "__main__":
    unittest.main()
