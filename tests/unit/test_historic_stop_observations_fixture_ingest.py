"""Unit tests for the S06 historic stop observations fixture ingest helpers."""

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

from muni_lta_pipeline.historic_stop_observations_fixture_ingest import (  # noqa: E402
    DEFAULT_FIXTURE_DIR,
    parse_observed_arrival_timestamp,
    parse_service_date,
    read_fixture_rows,
)


class HistoricStopObservationsFixtureIngestUnitTests(unittest.TestCase):
    def test_parse_service_date_requires_iso_date(self) -> None:
        parsed = parse_service_date("2026-05-01")
        self.assertEqual(parsed.isoformat(), "2026-05-01")

        with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
            parse_service_date("20260501")

    def test_parse_observed_arrival_timestamp_requires_timezone(self) -> None:
        parsed = parse_observed_arrival_timestamp("2026-05-01T08:01:15-07:00")
        self.assertEqual(parsed.isoformat(), "2026-05-01T08:01:15-07:00")

        with self.assertRaisesRegex(ValueError, "timezone offset"):
            parse_observed_arrival_timestamp("2026-05-01T08:01:15")

    def test_read_fixture_rows_parses_typed_fields(self) -> None:
        metadata = {
            "source_system": "511",
            "feed_scope": "regional_historic",
            "operator_id": "RG",
            "snapshot_label": "historic_2026_05_so_fixture_v1",
            "ingested_at": "2026-05-08T12:00:00+00:00",
        }
        rows = read_fixture_rows(DEFAULT_FIXTURE_DIR, metadata)

        self.assertEqual(len(rows), 3)
        row = rows[0]
        self.assertEqual(row["service_date"], "2026-05-01")
        self.assertEqual(row["stop_sequence"], "1")
        self.assertEqual(row["observed_arrival_ts"], "2026-05-01T08:01:15-07:00")
        self.assertEqual(row["feed_scope"], "regional_historic")


if __name__ == "__main__":
    unittest.main()
