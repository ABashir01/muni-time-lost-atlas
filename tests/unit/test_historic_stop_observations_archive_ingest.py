"""Unit tests for the real historic stop_observations archive ingest helpers."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import unittest


def _configure_src_paths() -> None:
    root = Path(__file__).resolve().parents[2]
    src_dir = root / "pipeline" / "src"
    src_str = str(src_dir)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)


_configure_src_paths()

from muni_lta_pipeline.historic_stop_observations_archive_ingest import (  # noqa: E402
    build_archive_snapshot_label,
    load_historic_archive_metadata,
    parse_compact_service_date,
    parse_service_day_observed_arrival_timestamp,
)


class HistoricStopObservationsArchiveIngestUnitTests(unittest.TestCase):
    def test_parse_compact_service_date_requires_yyyymmdd(self) -> None:
        parsed = parse_compact_service_date("20230214")
        self.assertEqual(parsed.isoformat(), "2023-02-14")

        with self.assertRaisesRegex(ValueError, "YYYYMMDD"):
            parse_compact_service_date("2023-02-14")

    def test_parse_service_day_timestamp_supports_post_midnight_hours(self) -> None:
        parsed = parse_service_day_observed_arrival_timestamp(
            "20230311",
            "25:15:00",
        )
        self.assertEqual(parsed.isoformat(), "2023-03-12T01:15:00-08:00")

    def test_load_historic_archive_metadata_requires_so_archive(self) -> None:
        workspace_tmp_root = Path(__file__).resolve().parents[2] / ".tmp"
        workspace_tmp_root.mkdir(parents=True, exist_ok=True)
        metadata_dir = workspace_tmp_root / "historic_stop_observations_archive_unit_test"
        shutil.rmtree(metadata_dir, ignore_errors=True)
        metadata_dir.mkdir(parents=True, exist_ok=True)
        metadata_path = metadata_dir / "archive.json"
        try:
            metadata_path.write_text(
                json.dumps(
                    {
                        "source_system": "511",
                        "feed_scope": "regional_historic",
                        "operator_id": "RG",
                        "artifact_filename": "archive.zip",
                        "requested_historic_month": "2023-02",
                        "requested_historic_value": "2023-02",
                        "requested_stop_observations": False,
                        "stop_observations_present": False,
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "'-so' archive request"):
                load_historic_archive_metadata(metadata_path)
        finally:
            shutil.rmtree(metadata_dir, ignore_errors=True)

    def test_build_archive_snapshot_label_uses_artifact_name(self) -> None:
        snapshot_label = build_archive_snapshot_label(
            {"artifact_filename": "511_regional_historic_RG_202302_with_so_20260508T223557Z.zip"}
        )
        self.assertEqual(
            snapshot_label,
            "archive_511_regional_historic_RG_202302_with_so_20260508T223557Z",
        )


if __name__ == "__main__":
    unittest.main()
