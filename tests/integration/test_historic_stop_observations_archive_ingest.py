"""Integration test for the real historic stop_observations archive ingest slice."""

from __future__ import annotations

import csv
from datetime import UTC, datetime
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
    parse_service_day_observed_arrival_timestamp,
)
from muni_lta_pipeline.historic_stop_observations_fixture_ingest import (  # noqa: E402
    load_historic_stop_observations_fixture,
)


REAL_LOAD_MAX_ROWS = 250


class HistoricStopObservationsArchiveIngestIntegrationTests(unittest.TestCase):
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
        load_historic_stop_observations_fixture()

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

            cls.expected_preview_row = cls._read_first_loadable_archive_row(
                acquisition_result.artifact_path
            )
            cls.load_result = load_historic_stop_observations_archive(
                metadata_path=acquisition_result.metadata_path,
                truncate=False,
                max_rows=REAL_LOAD_MAX_ROWS,
            )

    @staticmethod
    def _read_first_loadable_archive_row(artifact_path: Path) -> dict[str, str]:
        with zipfile.ZipFile(artifact_path, mode="r") as archive:
            with archive.open(STOP_OBSERVATIONS_FILENAME, mode="r") as raw_handle:
                reader = csv.DictReader(
                    TextIOWrapper(raw_handle, encoding="utf-8", newline="")
                )
                for row in reader:
                    observed_arrival_time = (row.get("observed_arrival_time") or "").strip()
                    if not observed_arrival_time:
                        continue
                    return {
                        "service_date": row["service_date"].strip(),
                        "trip_id": row["trip_id"].strip(),
                        "stop_id": row["to_stop_id"].strip(),
                        "stop_sequence": row["stop_sequence"].strip(),
                        "observed_arrival_time": observed_arrival_time,
                        "observed_arrival_ts": parse_service_day_observed_arrival_timestamp(
                            row["service_date"].strip(),
                            observed_arrival_time,
                        ).isoformat(),
                    }

        raise AssertionError("The fetched historic archive did not contain a loadable observation row.")

    def test_real_archive_rows_are_loaded_into_raw_stop_observations(self) -> None:
        self.assertEqual(self.load_result.inserted_row_count, REAL_LOAD_MAX_ROWS)

        actual_count = int(
            run_psql_sql(
                self.settings,
                f"""
                SELECT COUNT(*)
                FROM raw.stop_observations
                WHERE snapshot_label = '{self.load_result.snapshot_label}';
                """,
            )
        )
        self.assertEqual(actual_count, REAL_LOAD_MAX_ROWS)

    def test_loaded_real_archive_row_preserves_required_fields_and_timestamp(self) -> None:
        preview = self.expected_preview_row
        expected_utc_timestamp = (
            datetime.fromisoformat(preview["observed_arrival_ts"])
            .astimezone(UTC)
            .strftime("%Y-%m-%d %H:%M:%S")
        )
        loaded_values = run_psql_sql(
            self.settings,
            f"""
            SELECT
                service_date::TEXT,
                trip_id,
                stop_id,
                stop_sequence::TEXT,
                observed_arrival_time,
                TO_CHAR(observed_arrival_ts AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS')
            FROM raw.stop_observations
            WHERE snapshot_label = '{self.load_result.snapshot_label}'
              AND trip_id = '{preview["trip_id"]}'
              AND stop_id = '{preview["stop_id"]}'
              AND stop_sequence = {preview["stop_sequence"]}
            ORDER BY observed_arrival_ts
            LIMIT 1;
            """,
        ).split("|")

        self.assertEqual(loaded_values[0], "2023-02-14")
        self.assertEqual(loaded_values[1], preview["trip_id"])
        self.assertEqual(loaded_values[2], preview["stop_id"])
        self.assertEqual(loaded_values[3], preview["stop_sequence"])
        self.assertEqual(loaded_values[4], preview["observed_arrival_time"])
        self.assertEqual(loaded_values[5], expected_utc_timestamp)

    def test_snapshot_labels_distinguish_fixture_and_real_archive_loads(self) -> None:
        snapshot_rows = run_psql_sql(
            self.settings,
            """
            SELECT snapshot_label, COUNT(*)
            FROM raw.stop_observations
            GROUP BY snapshot_label
            ORDER BY snapshot_label;
            """,
        ).splitlines()

        self.assertIn("historic_2026_05_so_fixture_v1|3", snapshot_rows)
        self.assertIn(
            f"{self.load_result.snapshot_label}|{REAL_LOAD_MAX_ROWS}",
            snapshot_rows,
        )
        self.assertTrue(self.load_result.snapshot_label.startswith("archive_511_regional_historic_RG_202302_with_so_"))


if __name__ == "__main__":
    unittest.main()
