"""Tests for deriving an SF-only historic archive from a regional RG archive."""

from __future__ import annotations

import csv
from io import BytesIO, TextIOWrapper
import json
from pathlib import Path
import shutil
import sys
import unittest
import zipfile


def _configure_src_paths() -> None:
    root = Path(__file__).resolve().parents[2]
    for src_dir in (root / "api" / "src", root / "pipeline" / "src"):
        src_str = str(src_dir)
        if src_str not in sys.path:
            sys.path.insert(0, src_str)


_configure_src_paths()

from muni_lta_pipeline.historic_rg_feed_fetch import STOP_OBSERVATIONS_FILENAME  # noqa: E402
from muni_lta_pipeline.historic_rg_sf_extract import (  # noqa: E402
    DERIVED_FEED_SCOPE,
    extract_sf_historic_archive,
)


def _make_regional_archive_bytes() -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, mode="w") as archive:
        archive.writestr(
            "routes.txt",
            (
                "route_id,agency_id,route_short_name,route_long_name,route_type\n"
                "SF:1,SF,1,California,3\n"
                "AC:200,AC,200,Telegraph,3\n"
            ),
        )
        archive.writestr(
            "trips.txt",
            (
                "route_id,service_id,trip_id,trip_headsign,direction_id,shape_id\n"
                "SF:1,SF:SVC:20230215,SF:TRIP1:20230215,Downtown,1,SF:SHAPE1:20230215\n"
                "AC:200,AC:SVC:20230215,AC:TRIP1:20230215,Uptown,0,AC:SHAPE1:20230215\n"
            ),
        )
        archive.writestr(
            "stops.txt",
            (
                "stop_id,stop_name,stop_lat,stop_lon\n"
                "SF:STOP1,Market,37.0,-122.0\n"
                "SF:STOP2,Van Ness,37.1,-122.1\n"
                "AC:STOP1,Telegraph,37.2,-122.2\n"
            ),
        )
        archive.writestr(
            "stop_times.txt",
            (
                "trip_id,stop_id,stop_sequence,arrival_time,departure_time\n"
                "SF:TRIP1:20230215,SF:STOP1,1,08:00:00,08:00:00\n"
                "SF:TRIP1:20230215,SF:STOP2,2,08:10:00,08:10:00\n"
                "AC:TRIP1:20230215,AC:STOP1,1,09:00:00,09:00:00\n"
            ),
        )
        archive.writestr(
            "shapes.txt",
            (
                "shape_id,shape_pt_lat,shape_pt_lon,shape_pt_sequence\n"
                "SF:SHAPE1:20230215,37.0,-122.0,1\n"
                "AC:SHAPE1:20230215,37.2,-122.2,1\n"
            ),
        )
        archive.writestr(
            "calendar_dates.txt",
            (
                "service_id,date,exception_type\n"
                "SF:SVC:20230215,20230215,1\n"
                "AC:SVC:20230215,20230215,1\n"
            ),
        )
        archive.writestr(
            STOP_OBSERVATIONS_FILENAME,
            (
                "trip_id,trip_start_time,schedule_relationship,service_date,vehicle_id,stop_sequence,"
                "observed_arrival_time,observed_departure_time,uncertainty,dwell_time_secs,"
                "scheduled_dwell_time_secs,route_id,agency_id,direction_id,from_stop_id,to_stop_id,"
                "scheduled_arrival_time,scheduled_departure_time\n"
                "SF:TRIP1:20230215,,1,20230214,100,1,08:01:00,08:01:00,0,0,,SF:1,SF,1,,SF:STOP1,,\n"
                "AC:TRIP1:20230215,,1,20230214,200,1,09:01:00,09:01:00,0,0,,AC:200,AC,0,,AC:STOP1,,\n"
            ),
        )
    return buffer.getvalue()


def _read_member_rows(archive_path: Path, member_name: str) -> list[dict[str, str]]:
    with zipfile.ZipFile(archive_path, mode="r") as archive:
        with archive.open(member_name, mode="r") as raw_handle:
            reader = csv.DictReader(TextIOWrapper(raw_handle, encoding="utf-8", newline=""))
            return list(reader)


class HistoricRgSfExtractTests(unittest.TestCase):
    def test_extract_sf_historic_archive_filters_to_sf_rows(self) -> None:
        workspace_tmp_root = Path(__file__).resolve().parents[2] / ".tmp"
        workspace_tmp_root.mkdir(parents=True, exist_ok=True)
        source_root = workspace_tmp_root / "historic_rg_sf_extract_source"
        output_root = workspace_tmp_root / "historic_rg_sf_extract_output"
        shutil.rmtree(source_root, ignore_errors=True)
        shutil.rmtree(output_root, ignore_errors=True)
        source_root.mkdir(parents=True, exist_ok=True)
        output_root.mkdir(parents=True, exist_ok=True)

        try:
            artifact_path = source_root / "511_regional_historic_RG_202302_with_so_test.zip"
            artifact_path.write_bytes(_make_regional_archive_bytes())
            metadata_path = source_root / "511_regional_historic_RG_202302_with_so_test.json"
            metadata_path.write_text(
                json.dumps(
                    {
                        "source_system": "511",
                        "feed_scope": "regional_historic",
                        "operator_id": "RG",
                        "artifact_filename": artifact_path.name,
                        "requested_historic_month": "2023-02",
                        "requested_historic_value": "2023-02-so",
                        "requested_stop_observations": True,
                        "stop_observations_present": True,
                    },
                    indent=2,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            result = extract_sf_historic_archive(
                metadata_path=metadata_path,
                acquisitions_root=output_root,
            )

            self.assertFalse(result.reused_existing)
            self.assertEqual(result.metadata.feed_scope, DERIVED_FEED_SCOPE)
            self.assertEqual(result.metadata.operator_id, "SF")
            self.assertEqual(result.metadata.selected_agency_id, "SF")
            self.assertEqual(result.metadata.retained_row_counts["routes.txt"], 1)
            self.assertEqual(result.metadata.retained_row_counts["trips.txt"], 1)
            self.assertEqual(result.metadata.retained_row_counts["stop_times.txt"], 2)
            self.assertEqual(result.metadata.retained_row_counts["stops.txt"], 2)
            self.assertEqual(result.metadata.retained_row_counts["shapes.txt"], 1)
            self.assertEqual(result.metadata.retained_row_counts["calendar_dates.txt"], 1)
            self.assertEqual(result.metadata.retained_row_counts[STOP_OBSERVATIONS_FILENAME], 1)

            route_rows = _read_member_rows(result.artifact_path, "routes.txt")
            trip_rows = _read_member_rows(result.artifact_path, "trips.txt")
            stop_rows = _read_member_rows(result.artifact_path, "stops.txt")
            observed_rows = _read_member_rows(result.artifact_path, STOP_OBSERVATIONS_FILENAME)

            self.assertEqual([row["route_id"] for row in route_rows], ["SF:1"])
            self.assertEqual([row["trip_id"] for row in trip_rows], ["SF:TRIP1:20230215"])
            self.assertEqual(
                sorted(row["stop_id"] for row in stop_rows),
                ["SF:STOP1", "SF:STOP2"],
            )
            self.assertEqual([row["agency_id"] for row in observed_rows], ["SF"])

            reused_result = extract_sf_historic_archive(
                metadata_path=metadata_path,
                acquisitions_root=output_root,
            )
            self.assertTrue(reused_result.reused_existing)
            self.assertEqual(reused_result.metadata.artifact_filename, result.metadata.artifact_filename)
        finally:
            shutil.rmtree(source_root, ignore_errors=True)
            shutil.rmtree(output_root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
