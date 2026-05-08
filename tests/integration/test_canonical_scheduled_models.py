"""Integration test for the S05 canonical scheduled models slice."""

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

from muni_lta_pipeline.canonical_scheduled_models import (  # noqa: E402
    materialize_canonical_scheduled_models,
)
from muni_lta_pipeline.gtfs_static_fixture_ingest import (  # noqa: E402
    get_postgres_settings,
    load_gtfs_static_fixture,
    run_psql_sql,
)


class CanonicalScheduledModelsIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        load_gtfs_static_fixture()
        materialize_canonical_scheduled_models()
        cls.settings = get_postgres_settings()

    def test_canonical_tables_are_queryable_with_expected_counts(self) -> None:
        expected_counts = {
            "canonical.scheduled_routes": 1,
            "canonical.scheduled_trips": 1,
            "canonical.scheduled_stops": 3,
            "canonical.service_dates": 20,
            "canonical.scheduled_stop_events": 60,
        }

        for table_name, expected_count in expected_counts.items():
            actual_count = int(run_psql_sql(self.settings, f"SELECT COUNT(*) FROM {table_name};"))
            self.assertEqual(actual_count, expected_count, table_name)

    def test_required_canonical_keys_are_unique_and_non_null(self) -> None:
        assertions = {
            "routes_unique": """
                SELECT COUNT(*) = COUNT(DISTINCT route_id)
                FROM canonical.scheduled_routes;
            """,
            "routes_non_null": """
                SELECT COUNT(*) = 0
                FROM canonical.scheduled_routes
                WHERE route_id IS NULL;
            """,
            "trips_unique": """
                SELECT COUNT(*) = COUNT(DISTINCT trip_id)
                FROM canonical.scheduled_trips;
            """,
            "trips_non_null": """
                SELECT COUNT(*) = 0
                FROM canonical.scheduled_trips
                WHERE trip_id IS NULL OR route_id IS NULL OR service_id IS NULL;
            """,
            "stops_unique": """
                SELECT COUNT(*) = COUNT(DISTINCT stop_id)
                FROM canonical.scheduled_stops;
            """,
            "stops_non_null": """
                SELECT COUNT(*) = 0
                FROM canonical.scheduled_stops
                WHERE stop_id IS NULL;
            """,
            "service_dates_unique": """
                SELECT COUNT(*) = COUNT(DISTINCT (service_id, service_date))
                FROM canonical.service_dates;
            """,
            "service_dates_non_null": """
                SELECT COUNT(*) = 0
                FROM canonical.service_dates
                WHERE service_id IS NULL OR service_date IS NULL;
            """,
            "events_unique": """
                SELECT COUNT(*) = COUNT(DISTINCT (trip_id, service_date, stop_sequence))
                FROM canonical.scheduled_stop_events;
            """,
            "events_non_null": """
                SELECT COUNT(*) = 0
                FROM canonical.scheduled_stop_events
                WHERE trip_id IS NULL
                   OR route_id IS NULL
                   OR service_id IS NULL
                   OR service_date IS NULL
                   OR stop_id IS NULL
                   OR stop_sequence IS NULL;
            """,
        }

        for name, sql in assertions.items():
            result = run_psql_sql(self.settings, sql).strip().lower()
            self.assertEqual(result, "t", name)

    def test_canonical_references_hold_and_fixture_service_exception_is_applied(self) -> None:
        orphan_trip_route_count = int(
            run_psql_sql(
                self.settings,
                """
                SELECT COUNT(*)
                FROM canonical.scheduled_trips AS trips
                LEFT JOIN canonical.scheduled_routes AS routes
                  ON trips.route_id = routes.route_id
                WHERE routes.route_id IS NULL;
                """,
            )
        )
        orphan_event_trip_count = int(
            run_psql_sql(
                self.settings,
                """
                SELECT COUNT(*)
                FROM canonical.scheduled_stop_events AS events
                LEFT JOIN canonical.scheduled_trips AS trips
                  ON events.trip_id = trips.trip_id
                WHERE trips.trip_id IS NULL;
                """,
            )
        )
        orphan_event_stop_count = int(
            run_psql_sql(
                self.settings,
                """
                SELECT COUNT(*)
                FROM canonical.scheduled_stop_events AS events
                LEFT JOIN canonical.scheduled_stops AS stops
                  ON events.stop_id = stops.stop_id
                WHERE stops.stop_id IS NULL;
                """,
            )
        )
        orphan_event_service_date_count = int(
            run_psql_sql(
                self.settings,
                """
                SELECT COUNT(*)
                FROM canonical.scheduled_stop_events AS events
                LEFT JOIN canonical.service_dates AS service_dates
                  ON events.service_id = service_dates.service_id
                 AND events.service_date = service_dates.service_date
                WHERE service_dates.service_id IS NULL;
                """,
            )
        )
        removed_holiday_count = int(
            run_psql_sql(
                self.settings,
                """
                SELECT COUNT(*)
                FROM canonical.service_dates
                WHERE service_id = 'WKDY'
                  AND service_date = DATE '2026-05-25';
                """,
            )
        )

        self.assertEqual(orphan_trip_route_count, 0)
        self.assertEqual(orphan_event_trip_count, 0)
        self.assertEqual(orphan_event_stop_count, 0)
        self.assertEqual(orphan_event_service_date_count, 0)
        self.assertEqual(removed_holiday_count, 0)

    def test_scheduled_stop_events_expose_normalized_time_fields(self) -> None:
        row = run_psql_sql(
            self.settings,
            """
            SELECT trip_id, service_date, stop_sequence, arrival_time_secs, departure_time_secs
            FROM canonical.scheduled_stop_events
            WHERE trip_id = '14_WKDY_IB_0800'
              AND service_date = DATE '2026-05-01'
              AND stop_sequence = 1;
            """,
        )

        self.assertEqual(row, "14_WKDY_IB_0800|2026-05-01|1|28800|28800")
