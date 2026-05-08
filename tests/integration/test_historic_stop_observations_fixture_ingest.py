"""Integration test for the S06 historic stop observations fixture ingest slice."""

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
from muni_lta_pipeline.historic_stop_observations_fixture_ingest import (  # noqa: E402
    load_historic_stop_observations_fixture,
)


class HistoricStopObservationsFixtureIngestIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        load_gtfs_static_fixture()
        cls.load_counts = load_historic_stop_observations_fixture()
        cls.settings = get_postgres_settings()

    def test_loaded_row_counts_match_fixture(self) -> None:
        expected_counts = {"raw.stop_observations": 3}
        self.assertEqual(self.load_counts, expected_counts)

        actual_count = int(
            run_psql_sql(self.settings, "SELECT COUNT(*) FROM raw.stop_observations;")
        )
        self.assertEqual(actual_count, 3)

    def test_required_fields_are_not_null(self) -> None:
        null_count = int(
            run_psql_sql(
                self.settings,
                """
                SELECT COUNT(*)
                FROM raw.stop_observations
                WHERE service_date IS NULL
                   OR trip_id IS NULL
                   OR stop_id IS NULL
                   OR stop_sequence IS NULL
                   OR observed_arrival_time IS NULL
                   OR observed_arrival_ts IS NULL;
                """,
            )
        )

        self.assertEqual(null_count, 0)

    def test_timestamp_parsing_and_join_keys_are_usable(self) -> None:
        parsed_values = run_psql_sql(
            self.settings,
            """
            SELECT
                service_date::TEXT,
                stop_sequence::TEXT,
                TO_CHAR(observed_arrival_ts AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS')
            FROM raw.stop_observations
            ORDER BY stop_sequence
            LIMIT 1;
            """,
        ).split("|")

        self.assertEqual(parsed_values[0], "2026-05-01")
        self.assertEqual(parsed_values[1], "1")
        self.assertEqual(parsed_values[2], "2026-05-01 15:01:15")

        joinable_count = int(
            run_psql_sql(
                self.settings,
                """
                SELECT COUNT(*)
                FROM raw.stop_observations AS observations
                JOIN raw.gtfs_stop_times AS stop_times
                  ON observations.trip_id = stop_times.trip_id
                 AND observations.stop_id = stop_times.stop_id
                 AND observations.stop_sequence::TEXT = stop_times.stop_sequence;
                """,
            )
        )

        self.assertEqual(joinable_count, 3)


if __name__ == "__main__":
    unittest.main()
