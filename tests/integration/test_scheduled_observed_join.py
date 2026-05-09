"""Integration tests for the S07 scheduled/observed stop-event join slice."""

from __future__ import annotations

import csv
from io import TextIOWrapper
from pathlib import Path
import sys
import tempfile
import unittest
from urllib.error import URLError
import zipfile


def _configure_src_paths() -> None:
    root = Path(__file__).resolve().parents[2]
    src_dir = root / "pipeline" / "src"
    src_str = str(src_dir)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)


_configure_src_paths()

from muni_lta_pipeline.active_gtfs_fetch import get_511_api_key  # noqa: E402
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
from muni_lta_pipeline.historic_rg_feed_fetch import (  # noqa: E402
    STOP_OBSERVATIONS_FILENAME,
    fetch_historic_rg_gtfs_archive,
)
from muni_lta_pipeline.historic_stop_observations_archive_ingest import (  # noqa: E402
    load_historic_stop_observations_archive,
)
from muni_lta_pipeline.historic_stop_observations_fixture_ingest import (  # noqa: E402
    load_historic_stop_observations_fixture,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
JOIN_VALIDATION_FIXTURE_DIR = (
    REPO_ROOT / "fixtures" / "stop_observations" / "regional_rg_join_validation"
)
REAL_JOIN_MAX_ROWS = 25


class ScheduledObservedJoinIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        load_gtfs_static_fixture()
        materialize_canonical_scheduled_models()
        load_historic_stop_observations_fixture()
        materialize_canonical_observed_stop_events()
        cls.settings = get_postgres_settings()

    def test_fixture_rows_materialize_as_exact_joined_observed_events(self) -> None:
        matched_count = int(
            run_psql_sql(
                self.settings,
                "SELECT COUNT(*) FROM canonical.observed_stop_events;",
            )
        )
        self.assertEqual(matched_count, 3)

        summary_rows = run_psql_sql(
            self.settings,
            """
            SELECT observed_snapshot_label, join_status, row_count
            FROM canonical.observed_stop_event_join_summary
            ORDER BY observed_snapshot_label, join_status;
            """,
        ).splitlines()
        self.assertEqual(
            summary_rows,
            ["historic_2026_05_so_fixture_v1|matched_exact|3"],
        )

    def test_joined_rows_expose_scheduled_and_observed_timestamps_for_runtime_work(self) -> None:
        row = run_psql_sql(
            self.settings,
            """
            SELECT
                trip_id,
                stop_id,
                stop_sequence,
                TO_CHAR(scheduled_arrival_ts AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS'),
                TO_CHAR(observed_arrival_ts AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS'),
                arrival_delay_secs::TEXT
            FROM canonical.observed_stop_events
            WHERE trip_id = '14_WKDY_IB_0800'
              AND service_date = DATE '2026-05-01'
              AND stop_sequence = 1;
            """,
        )

        self.assertEqual(
            row,
            "14_WKDY_IB_0800|STP_24TH|1|2026-05-01 15:00:00|2026-05-01 15:01:15|75",
        )


class ScheduledObservedJoinMismatchIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        load_gtfs_static_fixture()
        materialize_canonical_scheduled_models()
        load_historic_stop_observations_fixture(
            fixture_dir=JOIN_VALIDATION_FIXTURE_DIR,
            snapshot_label="historic_2026_05_so_join_validation_v1",
        )
        materialize_canonical_observed_stop_events()
        cls.settings = get_postgres_settings()

    def test_unmatched_rows_are_surfaced_with_explicit_join_statuses(self) -> None:
        summary_rows = run_psql_sql(
            self.settings,
            """
            SELECT join_status, row_count
            FROM canonical.observed_stop_event_join_summary
            WHERE observed_snapshot_label = 'historic_2026_05_so_join_validation_v1'
            ORDER BY join_status;
            """,
        ).splitlines()

        self.assertEqual(
            summary_rows,
            [
                "matched_exact|3",
                "unmatched_stop_id|1",
                "unmatched_trip_service_date|1",
            ],
        )

    def test_unmatched_rows_do_not_silently_enter_canonical_observed_stop_events(self) -> None:
        row = run_psql_sql(
            self.settings,
            """
            SELECT join_status
            FROM canonical.observed_stop_event_join_audit
            WHERE observed_snapshot_label = 'historic_2026_05_so_join_validation_v1'
              AND trip_id = '14_WKDY_IB_0800'
              AND stop_sequence = 2
              AND observed_stop_id = 'STP_WRONG';
            """,
        )
        self.assertEqual(row, "unmatched_stop_id")

        matched_count = int(
            run_psql_sql(
                self.settings,
                """
                SELECT COUNT(*)
                FROM canonical.observed_stop_events
                WHERE observed_snapshot_label = 'historic_2026_05_so_join_validation_v1';
                """,
            )
        )
        self.assertEqual(matched_count, 3)


class ScheduledObservedJoinRealArchiveIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            api_key = get_511_api_key()
        except ValueError as exc:
            raise unittest.SkipTest(str(exc)) from exc

        if api_key == "replace_with_local_511_token":
            raise unittest.SkipTest(
                "TRANSIT_511_API_KEY is still the placeholder example value."
            )

        load_gtfs_static_fixture()
        materialize_canonical_scheduled_models()
        cls.settings = get_postgres_settings()

        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                acquisition_result = fetch_historic_rg_gtfs_archive(
                    api_key=api_key,
                    historic_month="2023-02",
                    include_stop_observations=True,
                    acquisitions_root=Path(tmpdir),
                    timeout_seconds=120,
                )
            except URLError as exc:
                raise unittest.SkipTest(
                    f"Network access to 511 is not available in this environment: {exc}"
                ) from exc

            cls.preview_loadable_row_count = cls._count_loadable_archive_rows(
                acquisition_result.artifact_path
            )
            cls.load_result = load_historic_stop_observations_archive(
                metadata_path=acquisition_result.metadata_path,
                max_rows=REAL_JOIN_MAX_ROWS,
            )

        materialize_canonical_observed_stop_events()

    @staticmethod
    def _count_loadable_archive_rows(artifact_path: Path) -> int:
        loadable_row_count = 0
        with zipfile.ZipFile(artifact_path, mode="r") as archive:
            with archive.open(STOP_OBSERVATIONS_FILENAME, mode="r") as raw_handle:
                reader = csv.DictReader(
                    TextIOWrapper(raw_handle, encoding="utf-8", newline="")
                )
                for row in reader:
                    if (row.get("observed_arrival_time") or "").strip():
                        loadable_row_count += 1
                    if loadable_row_count >= REAL_JOIN_MAX_ROWS:
                        return loadable_row_count

        return loadable_row_count

    def test_real_archive_rows_surface_as_unmatched_until_historic_schedule_reconciliation_exists(self) -> None:
        self.assertEqual(
            self.load_result.inserted_row_count,
            self.preview_loadable_row_count,
        )

        summary_rows = run_psql_sql(
            self.settings,
            f"""
            SELECT join_status, row_count
            FROM canonical.observed_stop_event_join_summary
            WHERE observed_snapshot_label = '{self.load_result.snapshot_label}'
            ORDER BY join_status;
            """,
        ).splitlines()

        self.assertEqual(
            summary_rows,
            [f"unmatched_trip_service_date|{self.load_result.inserted_row_count}"],
        )


if __name__ == "__main__":
    unittest.main()
