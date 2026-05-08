"""Integration test for the S04 GTFS static fixture ingest slice."""

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

from muni_lta_pipeline.gtfs_static_fixture_ingest import (  # noqa: E402
    get_postgres_settings,
    load_gtfs_static_fixture,
    run_psql_sql,
)


class GtfsStaticFixtureIngestIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.load_counts = load_gtfs_static_fixture()
        cls.settings = get_postgres_settings()

    def test_loaded_row_counts_match_fixture(self) -> None:
        expected_counts = {
            "raw.gtfs_routes": 1,
            "raw.gtfs_trips": 1,
            "raw.gtfs_stops": 3,
            "raw.gtfs_stop_times": 3,
            "raw.gtfs_shapes": 3,
            "raw.gtfs_calendar": 1,
            "raw.gtfs_calendar_dates": 1,
        }

        self.assertEqual(self.load_counts, expected_counts)

        for table_name, expected_count in expected_counts.items():
            actual_count = int(run_psql_sql(self.settings, f"SELECT COUNT(*) FROM {table_name};"))
            self.assertEqual(actual_count, expected_count, table_name)

    def test_raw_stop_times_preserves_source_column_names(self) -> None:
        column_names = set(
            run_psql_sql(
                self.settings,
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'raw'
                  AND table_name = 'gtfs_stop_times';
                """,
            ).splitlines()
        )

        self.assertIn("arrival_time", column_names)
        self.assertIn("departure_time", column_names)
        self.assertNotIn("arrival_time_text", column_names)
        self.assertNotIn("departure_time_text", column_names)

    def test_referential_sanity_between_trips_stop_times_and_stops(self) -> None:
        orphan_trip_count = int(
            run_psql_sql(
                self.settings,
                """
                SELECT COUNT(*)
                FROM raw.gtfs_stop_times AS stop_times
                LEFT JOIN raw.gtfs_trips AS trips
                  ON stop_times.trip_id = trips.trip_id
                WHERE trips.trip_id IS NULL;
                """,
            )
        )
        orphan_stop_count = int(
            run_psql_sql(
                self.settings,
                """
                SELECT COUNT(*)
                FROM raw.gtfs_stop_times AS stop_times
                LEFT JOIN raw.gtfs_stops AS stops
                  ON stop_times.stop_id = stops.stop_id
                WHERE stops.stop_id IS NULL;
                """,
            )
        )
        orphan_route_count = int(
            run_psql_sql(
                self.settings,
                """
                SELECT COUNT(*)
                FROM raw.gtfs_trips AS trips
                LEFT JOIN raw.gtfs_routes AS routes
                  ON trips.route_id = routes.route_id
                WHERE routes.route_id IS NULL;
                """,
            )
        )

        self.assertEqual(orphan_trip_count, 0)
        self.assertEqual(orphan_stop_count, 0)
        self.assertEqual(orphan_route_count, 0)
