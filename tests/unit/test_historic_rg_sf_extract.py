"""Tests for deriving an SF-only historic archive from a regional RG archive."""

from __future__ import annotations

import csv
import hashlib
from io import BytesIO, TextIOWrapper
import json
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
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
    _build_shape_pattern_id,
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


def _make_regional_archive_bytes_without_shapes() -> bytes:
    payload = _make_regional_archive_bytes()
    source_buffer = BytesIO(payload)
    destination_buffer = BytesIO()
    with zipfile.ZipFile(source_buffer, mode="r") as source_archive:
        with zipfile.ZipFile(destination_buffer, mode="w") as destination_archive:
            for member_name in source_archive.namelist():
                if member_name == "shapes.txt":
                    continue
                destination_archive.writestr(member_name, source_archive.read(member_name))
    return destination_buffer.getvalue()


def _make_regional_archive_bytes_without_shapes_or_shape_ids() -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, mode="w") as archive:
        archive.writestr(
            "routes.txt",
            (
                "route_id,agency_id,route_short_name,route_long_name,route_type\n"
                "SF:1,SF,1,California,3\n"
            ),
        )
        archive.writestr(
            "trips.txt",
            "route_id,service_id,trip_id,trip_headsign,direction_id,shape_id\n"
            "SF:1,SF:SVC:20260415,SF:TRIP1:20260415,Downtown,1,\n",
        )
        archive.writestr(
            "stops.txt",
            "stop_id,stop_name,stop_lat,stop_lon\n"
            "SF:STOP1,Market,37.0,-122.0\n",
        )
        archive.writestr(
            "stop_times.txt",
            "trip_id,stop_id,stop_sequence,arrival_time,departure_time\n"
            "SF:TRIP1:20260415,SF:STOP1,1,08:00:00,08:00:00\n",
        )
        archive.writestr(
            "calendar_dates.txt",
            "service_id,date,exception_type\n"
            "SF:SVC:20260415,20260415,1\n",
        )
        archive.writestr(
            STOP_OBSERVATIONS_FILENAME,
            "trip_id,trip_start_time,schedule_relationship,service_date,vehicle_id,stop_sequence,"
            "observed_arrival_time,observed_departure_time,uncertainty,dwell_time_secs,"
            "scheduled_dwell_time_secs,route_id,agency_id,direction_id,from_stop_id,to_stop_id,"
            "scheduled_arrival_time,scheduled_departure_time\n"
            "SF:TRIP1:20260415,,1,20260414,100,1,08:01:00,08:01:00,0,0,,SF:1,SF,1,,SF:STOP1,,\n",
        )
    return buffer.getvalue()


def _make_regional_archive_bytes_without_shapes_or_shape_ids_two_trips_same_headsign() -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, mode="w") as archive:
        archive.writestr(
            "routes.txt",
            (
                "route_id,agency_id,route_short_name,route_long_name,route_type\n"
                "SF:1,SF,1,California,3\n"
            ),
        )
        archive.writestr(
            "trips.txt",
            "route_id,service_id,trip_id,trip_headsign,direction_id,shape_id\n"
            "SF:1,SF:SVC:20260415,SF:TRIP1:20260415,Downtown,1,\n"
            "SF:1,SF:SVC:20260415,SF:TRIP2:20260415,Downtown,1,\n",
        )
        archive.writestr(
            "stops.txt",
            "stop_id,stop_name,stop_lat,stop_lon\n"
            "SF:STOP1,Market,37.0,-122.0\n"
            "SF:STOP2,Van Ness,37.1,-122.1\n",
        )
        archive.writestr(
            "stop_times.txt",
            "trip_id,stop_id,stop_sequence,arrival_time,departure_time\n"
            "SF:TRIP1:20260415,SF:STOP1,1,08:00:00,08:00:00\n"
            "SF:TRIP1:20260415,SF:STOP2,2,08:10:00,08:10:00\n"
            "SF:TRIP2:20260415,SF:STOP2,1,08:30:00,08:30:00\n"
            "SF:TRIP2:20260415,SF:STOP1,2,08:40:00,08:40:00\n",
        )
        archive.writestr(
            "calendar_dates.txt",
            "service_id,date,exception_type\n"
            "SF:SVC:20260415,20260415,1\n",
        )
        archive.writestr(
            STOP_OBSERVATIONS_FILENAME,
            "trip_id,trip_start_time,schedule_relationship,service_date,vehicle_id,stop_sequence,"
            "observed_arrival_time,observed_departure_time,uncertainty,dwell_time_secs,"
            "scheduled_dwell_time_secs,route_id,agency_id,direction_id,from_stop_id,to_stop_id,"
            "scheduled_arrival_time,scheduled_departure_time\n"
            "SF:TRIP1:20260415,,1,20260414,100,1,08:01:00,08:01:00,0,0,,SF:1,SF,1,,SF:STOP1,,\n"
            "SF:TRIP2:20260415,,1,20260414,101,1,08:31:00,08:31:00,0,0,,SF:1,SF,1,,SF:STOP1,,\n",
        )
    return buffer.getvalue()


def _make_active_archive_bytes() -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, mode="w") as archive:
        archive.writestr(
            "routes.txt",
            (
                "route_id,agency_id,route_short_name,route_long_name,route_type\n"
                "1,SF,1,California,3\n"
            ),
        )
        archive.writestr(
            "trips.txt",
            "route_id,service_id,trip_id,trip_headsign,direction_id,shape_id\n"
            "1,ACTIVE1,ACTIVE_TRIP_A,Downtown,1,ACTIVE_SHAPE\n"
            "1,ACTIVE2,ACTIVE_TRIP_B,Downtown,1,ACTIVE_SHAPE\n",
        )
        archive.writestr(
            "stops.txt",
            "stop_id,stop_name,stop_lat,stop_lon\n"
            "SF:STOP1,Market,37.0,-122.0\n",
        )
        archive.writestr(
            "stop_times.txt",
            "trip_id,stop_id,stop_sequence,arrival_time,departure_time\n"
            "ACTIVE_TRIP_A,SF:STOP1,1,08:00:00,08:00:00\n",
        )
        archive.writestr(
            "shapes.txt",
            "shape_id,shape_pt_lat,shape_pt_lon,shape_pt_sequence\n"
            "ACTIVE_SHAPE,37.0,-122.0,1\n",
        )
        archive.writestr(
            "calendar_dates.txt",
            "service_id,date,exception_type\n"
            "ACTIVE1,20260523,1\n",
        )
    return buffer.getvalue()


def _read_member_rows(archive_path: Path, member_name: str) -> list[dict[str, str]]:
    with zipfile.ZipFile(archive_path, mode="r") as archive:
        with archive.open(member_name, mode="r") as raw_handle:
            reader = csv.DictReader(TextIOWrapper(raw_handle, encoding="utf-8", newline=""))
            return list(reader)


def _stop_pattern_key(*values: str) -> str:
    return hashlib.sha256("\n".join(values).encode("utf-8")).hexdigest()[:16]


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

    def test_extract_sf_historic_archive_backfills_missing_shapes_via_shapes_api_cache(self) -> None:
        workspace_tmp_root = Path(__file__).resolve().parents[2] / ".tmp"
        workspace_tmp_root.mkdir(parents=True, exist_ok=True)
        source_root = workspace_tmp_root / "historic_rg_sf_extract_shapes_source"
        output_root = workspace_tmp_root / "historic_rg_sf_extract_shapes_output"
        cache_root = workspace_tmp_root / "historic_rg_sf_extract_shapes_cache"
        shutil.rmtree(source_root, ignore_errors=True)
        shutil.rmtree(output_root, ignore_errors=True)
        shutil.rmtree(cache_root, ignore_errors=True)
        source_root.mkdir(parents=True, exist_ok=True)
        output_root.mkdir(parents=True, exist_ok=True)
        cache_root.mkdir(parents=True, exist_ok=True)

        try:
            artifact_path = source_root / "511_regional_historic_RG_202604_with_so_test.zip"
            artifact_path.write_bytes(_make_regional_archive_bytes_without_shapes())
            metadata_path = source_root / "511_regional_historic_RG_202604_with_so_test.json"
            metadata_path.write_text(
                json.dumps(
                    {
                        "source_system": "511",
                        "feed_scope": "regional_historic",
                        "operator_id": "RG",
                        "artifact_filename": artifact_path.name,
                        "requested_historic_month": "2026-04",
                        "requested_historic_value": "2026-04-so",
                        "requested_stop_observations": True,
                        "stop_observations_present": True,
                        "shapes_present": False,
                    },
                    indent=2,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            with patch(
                "muni_lta_pipeline.historic_rg_sf_extract.backfill_missing_shapes",
                return_value=SimpleNamespace(
                    shape_rows=(
                        {
                            "shape_id": "SF:SHAPE1:20230215",
                            "shape_pt_lat": "37.0",
                            "shape_pt_lon": "-122.0",
                            "shape_pt_sequence": "1",
                            "shape_dist_traveled": "",
                        },
                    ),
                    request_count=1,
                    cache_hit_count=0,
                    successful_shape_count=1,
                    failure_shape_ids=(),
                    artifacts=(),
                ),
            ):
                result = extract_sf_historic_archive(
                    metadata_path=metadata_path,
                    acquisitions_root=output_root,
                    api_key="test-token",
                    shapes_cache_root=cache_root,
                )

            shape_rows = _read_member_rows(result.artifact_path, "shapes.txt")
            self.assertEqual(len(shape_rows), 1)
            self.assertEqual(shape_rows[0]["shape_id"], "SF:SHAPE1:20230215")
            self.assertTrue(result.metadata.shape_fallback_used)
            self.assertEqual(result.metadata.shape_backfill_request_count, 1)
            self.assertEqual(result.metadata.shape_backfill_shape_count, 1)
            self.assertTrue(Path(result.metadata.shape_backfill_manifest_path).exists())
        finally:
            shutil.rmtree(source_root, ignore_errors=True)
            shutil.rmtree(output_root, ignore_errors=True)
            shutil.rmtree(cache_root, ignore_errors=True)

    def test_extract_sf_historic_archive_fails_when_shape_backfill_is_incomplete(self) -> None:
        workspace_tmp_root = Path(__file__).resolve().parents[2] / ".tmp"
        workspace_tmp_root.mkdir(parents=True, exist_ok=True)
        source_root = workspace_tmp_root / "historic_rg_sf_extract_shapes_fail_source"
        output_root = workspace_tmp_root / "historic_rg_sf_extract_shapes_fail_output"
        cache_root = workspace_tmp_root / "historic_rg_sf_extract_shapes_fail_cache"
        shutil.rmtree(source_root, ignore_errors=True)
        shutil.rmtree(output_root, ignore_errors=True)
        shutil.rmtree(cache_root, ignore_errors=True)
        source_root.mkdir(parents=True, exist_ok=True)
        output_root.mkdir(parents=True, exist_ok=True)
        cache_root.mkdir(parents=True, exist_ok=True)

        try:
            artifact_path = source_root / "511_regional_historic_RG_202604_with_so_test.zip"
            artifact_path.write_bytes(_make_regional_archive_bytes_without_shapes())
            metadata_path = source_root / "511_regional_historic_RG_202604_with_so_test.json"
            metadata_path.write_text(
                json.dumps(
                    {
                        "source_system": "511",
                        "feed_scope": "regional_historic",
                        "operator_id": "RG",
                        "artifact_filename": artifact_path.name,
                        "requested_historic_month": "2026-04",
                        "requested_historic_value": "2026-04-so",
                        "requested_stop_observations": True,
                        "stop_observations_present": True,
                        "shapes_present": False,
                    },
                    indent=2,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            with patch(
                "muni_lta_pipeline.historic_rg_sf_extract.backfill_missing_shapes",
                return_value=SimpleNamespace(
                    shape_rows=(),
                    request_count=1,
                    cache_hit_count=0,
                    successful_shape_count=0,
                    failure_shape_ids=("SF:SHAPE1:20230215",),
                    artifacts=(),
                ),
            ):
                with self.assertRaisesRegex(RuntimeError, "Failed to backfill required Shapes API geometries"):
                    extract_sf_historic_archive(
                        metadata_path=metadata_path,
                        acquisitions_root=output_root,
                        api_key="test-token",
                        shapes_cache_root=cache_root,
                    )
        finally:
            shutil.rmtree(source_root, ignore_errors=True)
            shutil.rmtree(output_root, ignore_errors=True)
            shutil.rmtree(cache_root, ignore_errors=True)

    def test_extract_sf_historic_archive_synthesizes_shape_ids_when_source_trips_leave_them_blank(self) -> None:
        workspace_tmp_root = Path(__file__).resolve().parents[2] / ".tmp"
        workspace_tmp_root.mkdir(parents=True, exist_ok=True)
        source_root = workspace_tmp_root / "historic_rg_sf_extract_no_shape_ids_source"
        output_root = workspace_tmp_root / "historic_rg_sf_extract_no_shape_ids_output"
        cache_root = workspace_tmp_root / "historic_rg_sf_extract_no_shape_ids_cache"
        active_root = workspace_tmp_root / "historic_rg_sf_extract_no_shape_ids_active"
        shutil.rmtree(source_root, ignore_errors=True)
        shutil.rmtree(output_root, ignore_errors=True)
        shutil.rmtree(cache_root, ignore_errors=True)
        shutil.rmtree(active_root, ignore_errors=True)
        source_root.mkdir(parents=True, exist_ok=True)
        output_root.mkdir(parents=True, exist_ok=True)
        cache_root.mkdir(parents=True, exist_ok=True)
        active_root.mkdir(parents=True, exist_ok=True)

        try:
            artifact_path = source_root / "511_regional_historic_RG_202604_with_so_test.zip"
            artifact_path.write_bytes(_make_regional_archive_bytes_without_shapes_or_shape_ids())
            metadata_path = source_root / "511_regional_historic_RG_202604_with_so_test.json"
            metadata_path.write_text(
                json.dumps(
                    {
                        "source_system": "511",
                        "feed_scope": "regional_historic",
                        "operator_id": "RG",
                        "artifact_filename": artifact_path.name,
                        "requested_historic_month": "2026-04",
                        "requested_historic_value": "2026-04-so",
                        "requested_stop_observations": True,
                        "stop_observations_present": True,
                        "shapes_present": False,
                    },
                    indent=2,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            active_artifact_path = active_root / "511_operator_active_SF_test.zip"
            active_artifact_path.write_bytes(_make_active_archive_bytes())
            active_metadata_path = active_root / "511_operator_active_SF_test.json"
            active_metadata_path.write_text(
                json.dumps(
                    {
                        "source_system": "511",
                        "feed_scope": "operator_active",
                        "operator_id": "SF",
                        "artifact_filename": active_artifact_path.name,
                    },
                    indent=2,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            with patch(
                "muni_lta_pipeline.historic_rg_sf_extract.backfill_missing_shapes",
            ) as mock_backfill:
                result = extract_sf_historic_archive(
                    metadata_path=metadata_path,
                    acquisitions_root=output_root,
                    api_key="test-token",
                    shapes_cache_root=cache_root,
                    active_metadata_path=active_metadata_path,
                )

            trip_rows = _read_member_rows(result.artifact_path, "trips.txt")
            shape_rows = _read_member_rows(result.artifact_path, "shapes.txt")
            self.assertEqual(trip_rows[0]["shape_id"], "SF:active_shape:ACTIVE_SHAPE")
            self.assertEqual(shape_rows[0]["shape_id"], "SF:active_shape:ACTIVE_SHAPE")
            self.assertEqual(shape_rows[0]["shape_pt_sequence"], "1")
            self.assertTrue(result.metadata.shape_fallback_used)
            self.assertFalse(mock_backfill.called)
        finally:
            shutil.rmtree(source_root, ignore_errors=True)
            shutil.rmtree(output_root, ignore_errors=True)
            shutil.rmtree(cache_root, ignore_errors=True)
            shutil.rmtree(active_root, ignore_errors=True)

    def test_extract_sf_historic_archive_uses_active_trip_candidates_for_shapes_api_when_active_shape_rows_are_unavailable(self) -> None:
        workspace_tmp_root = Path(__file__).resolve().parents[2] / ".tmp"
        workspace_tmp_root.mkdir(parents=True, exist_ok=True)
        source_root = workspace_tmp_root / "historic_rg_sf_extract_active_candidate_source"
        output_root = workspace_tmp_root / "historic_rg_sf_extract_active_candidate_output"
        cache_root = workspace_tmp_root / "historic_rg_sf_extract_active_candidate_cache"
        shutil.rmtree(source_root, ignore_errors=True)
        shutil.rmtree(output_root, ignore_errors=True)
        shutil.rmtree(cache_root, ignore_errors=True)
        source_root.mkdir(parents=True, exist_ok=True)
        output_root.mkdir(parents=True, exist_ok=True)
        cache_root.mkdir(parents=True, exist_ok=True)

        try:
            artifact_path = source_root / "511_regional_historic_RG_202604_with_so_test.zip"
            artifact_path.write_bytes(_make_regional_archive_bytes_without_shapes_or_shape_ids())
            metadata_path = source_root / "511_regional_historic_RG_202604_with_so_test.json"
            metadata_path.write_text(
                json.dumps(
                    {
                        "source_system": "511",
                        "feed_scope": "regional_historic",
                        "operator_id": "RG",
                        "artifact_filename": artifact_path.name,
                        "requested_historic_month": "2026-04",
                        "requested_historic_value": "2026-04-so",
                        "requested_stop_observations": True,
                        "stop_observations_present": True,
                        "shapes_present": False,
                    },
                    indent=2,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            with (
                patch(
                    "muni_lta_pipeline.historic_rg_sf_extract._read_active_shape_fallback_data",
                    return_value=(
                        {("1", "1", "Downtown"): [("ACTIVE_TRIP_A", ""), ("ACTIVE_TRIP_B", "")]},
                        {("1", "1"): [("ACTIVE_TRIP_A", ""), ("ACTIVE_TRIP_B", "")]},
                        {
                            ("1", "1", "Downtown", _stop_pattern_key("1:SF:STOP1")): [
                                ("ACTIVE_TRIP_A", ""),
                                ("ACTIVE_TRIP_B", ""),
                            ]
                        },
                        {},
                        {},
                    ),
                ),
                patch(
                    "muni_lta_pipeline.historic_rg_sf_extract.backfill_missing_shapes",
                    return_value=SimpleNamespace(
                        shape_rows=(
                            {
                                "shape_id": _build_shape_pattern_id(
                                    selected_agency_id="SF",
                                    route_id="SF:1",
                                    direction_id="1",
                                    trip_headsign="Downtown",
                                    stop_pattern_key=_stop_pattern_key("1:SF:STOP1"),
                                ),
                                "shape_pt_lat": "37.0",
                                "shape_pt_lon": "-122.0",
                                "shape_pt_sequence": "1",
                                "shape_dist_traveled": "",
                            },
                        ),
                        request_count=1,
                        cache_hit_count=0,
                        successful_shape_count=1,
                        failure_shape_ids=(),
                        artifacts=(),
                    ),
                ) as mock_backfill,
            ):
                result = extract_sf_historic_archive(
                    metadata_path=metadata_path,
                    acquisitions_root=output_root,
                    api_key="test-token",
                    shapes_cache_root=cache_root,
                    active_metadata_path=source_root / "unused_active_metadata.json",
                )

            trip_rows = _read_member_rows(result.artifact_path, "trips.txt")
            shape_rows = _read_member_rows(result.artifact_path, "shapes.txt")
            expected_shape_id = _build_shape_pattern_id(
                selected_agency_id="SF",
                route_id="SF:1",
                direction_id="1",
                trip_headsign="Downtown",
                stop_pattern_key=_stop_pattern_key("1:SF:STOP1"),
            )
            self.assertEqual(trip_rows[0]["shape_id"], expected_shape_id)
            self.assertEqual(shape_rows[0]["shape_id"], expected_shape_id)
            self.assertEqual(
                mock_backfill.call_args.args[0],
                {expected_shape_id: ["SF:TRIP1:20260415", "ACTIVE_TRIP_A", "ACTIVE_TRIP_B"]},
            )
        finally:
            shutil.rmtree(source_root, ignore_errors=True)
            shutil.rmtree(output_root, ignore_errors=True)
            shutil.rmtree(cache_root, ignore_errors=True)

    def test_extract_sf_historic_archive_falls_back_to_route_direction_active_trip_candidates(self) -> None:
        workspace_tmp_root = Path(__file__).resolve().parents[2] / ".tmp"
        workspace_tmp_root.mkdir(parents=True, exist_ok=True)
        source_root = workspace_tmp_root / "historic_rg_sf_extract_route_direction_candidate_source"
        output_root = workspace_tmp_root / "historic_rg_sf_extract_route_direction_candidate_output"
        cache_root = workspace_tmp_root / "historic_rg_sf_extract_route_direction_candidate_cache"
        shutil.rmtree(source_root, ignore_errors=True)
        shutil.rmtree(output_root, ignore_errors=True)
        shutil.rmtree(cache_root, ignore_errors=True)
        source_root.mkdir(parents=True, exist_ok=True)
        output_root.mkdir(parents=True, exist_ok=True)
        cache_root.mkdir(parents=True, exist_ok=True)

        try:
            artifact_path = source_root / "511_regional_historic_RG_202604_with_so_test.zip"
            artifact_path.write_bytes(_make_regional_archive_bytes_without_shapes_or_shape_ids())
            metadata_path = source_root / "511_regional_historic_RG_202604_with_so_test.json"
            metadata_path.write_text(
                json.dumps(
                    {
                        "source_system": "511",
                        "feed_scope": "regional_historic",
                        "operator_id": "RG",
                        "artifact_filename": artifact_path.name,
                        "requested_historic_month": "2026-04",
                        "requested_historic_value": "2026-04-so",
                        "requested_stop_observations": True,
                        "stop_observations_present": True,
                        "shapes_present": False,
                    },
                    indent=2,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            with (
                patch(
                    "muni_lta_pipeline.historic_rg_sf_extract._read_active_shape_fallback_data",
                    return_value=(
                        {},
                        {("1", "1"): [("ACTIVE_TRIP_ROUTE_A", ""), ("ACTIVE_TRIP_ROUTE_B", "")]},
                        {},
                        {},
                        {},
                    ),
                ),
                patch(
                    "muni_lta_pipeline.historic_rg_sf_extract.backfill_missing_shapes",
                    return_value=SimpleNamespace(
                        shape_rows=(
                            {
                                "shape_id": _build_shape_pattern_id(
                                    selected_agency_id="SF",
                                    route_id="SF:1",
                                    direction_id="1",
                                    trip_headsign="Downtown",
                                    stop_pattern_key=_stop_pattern_key("1:SF:STOP1"),
                                ),
                                "shape_pt_lat": "37.0",
                                "shape_pt_lon": "-122.0",
                                "shape_pt_sequence": "1",
                                "shape_dist_traveled": "",
                            },
                        ),
                        request_count=1,
                        cache_hit_count=0,
                        successful_shape_count=1,
                        failure_shape_ids=(),
                        artifacts=(),
                    ),
                ) as mock_backfill,
            ):
                extract_sf_historic_archive(
                    metadata_path=metadata_path,
                    acquisitions_root=output_root,
                    api_key="test-token",
                    shapes_cache_root=cache_root,
                    active_metadata_path=source_root / "unused_active_metadata.json",
                )

            expected_shape_id = _build_shape_pattern_id(
                selected_agency_id="SF",
                route_id="SF:1",
                direction_id="1",
                trip_headsign="Downtown",
                stop_pattern_key=_stop_pattern_key("1:SF:STOP1"),
            )
            self.assertEqual(
                mock_backfill.call_args.args[0],
                {
                    expected_shape_id: [
                        "SF:TRIP1:20260415",
                        "ACTIVE_TRIP_ROUTE_A",
                        "ACTIVE_TRIP_ROUTE_B",
                    ]
                },
            )
        finally:
            shutil.rmtree(source_root, ignore_errors=True)
            shutil.rmtree(output_root, ignore_errors=True)
            shutil.rmtree(cache_root, ignore_errors=True)

    def test_extract_sf_historic_archive_does_not_reuse_ambiguous_active_shape_rows(self) -> None:
        workspace_tmp_root = Path(__file__).resolve().parents[2] / ".tmp"
        workspace_tmp_root.mkdir(parents=True, exist_ok=True)
        source_root = workspace_tmp_root / "historic_rg_sf_extract_ambiguous_active_source"
        output_root = workspace_tmp_root / "historic_rg_sf_extract_ambiguous_active_output"
        cache_root = workspace_tmp_root / "historic_rg_sf_extract_ambiguous_active_cache"
        shutil.rmtree(source_root, ignore_errors=True)
        shutil.rmtree(output_root, ignore_errors=True)
        shutil.rmtree(cache_root, ignore_errors=True)
        source_root.mkdir(parents=True, exist_ok=True)
        output_root.mkdir(parents=True, exist_ok=True)
        cache_root.mkdir(parents=True, exist_ok=True)

        try:
            artifact_path = source_root / "511_regional_historic_RG_202604_with_so_test.zip"
            artifact_path.write_bytes(_make_regional_archive_bytes_without_shapes_or_shape_ids())
            metadata_path = source_root / "511_regional_historic_RG_202604_with_so_test.json"
            metadata_path.write_text(
                json.dumps(
                    {
                        "source_system": "511",
                        "feed_scope": "regional_historic",
                        "operator_id": "RG",
                        "artifact_filename": artifact_path.name,
                        "requested_historic_month": "2026-04",
                        "requested_historic_value": "2026-04-so",
                        "requested_stop_observations": True,
                        "stop_observations_present": True,
                        "shapes_present": False,
                    },
                    indent=2,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            with (
                patch(
                    "muni_lta_pipeline.historic_rg_sf_extract._read_active_shape_fallback_data",
                    return_value=(
                        {("1", "1", "Downtown"): [("ACTIVE_TRIP_A", "SHAPE_A"), ("ACTIVE_TRIP_B", "SHAPE_B")]},
                        {("1", "1"): [("ACTIVE_TRIP_A", "SHAPE_A"), ("ACTIVE_TRIP_B", "SHAPE_B")]},
                        {
                            ("1", "1", "Downtown", _stop_pattern_key("1:SF:STOP1")): [
                                ("ACTIVE_TRIP_A", "SHAPE_A"),
                                ("ACTIVE_TRIP_B", "SHAPE_B"),
                            ]
                        },
                        {},
                        {
                            "SHAPE_A": [
                                {
                                    "shape_id": "SHAPE_A",
                                    "shape_pt_lat": "37.0",
                                    "shape_pt_lon": "-122.0",
                                    "shape_pt_sequence": "1",
                                    "shape_dist_traveled": "",
                                }
                            ],
                            "SHAPE_B": [
                                {
                                    "shape_id": "SHAPE_B",
                                    "shape_pt_lat": "37.1",
                                    "shape_pt_lon": "-122.1",
                                    "shape_pt_sequence": "1",
                                    "shape_dist_traveled": "",
                                }
                            ],
                        },
                    ),
                ),
                patch(
                    "muni_lta_pipeline.historic_rg_sf_extract.backfill_missing_shapes",
                    return_value=SimpleNamespace(
                        shape_rows=(
                            {
                                "shape_id": _build_shape_pattern_id(
                                    selected_agency_id="SF",
                                    route_id="SF:1",
                                    direction_id="1",
                                    trip_headsign="Downtown",
                                    stop_pattern_key=_stop_pattern_key("1:SF:STOP1"),
                                ),
                                "shape_pt_lat": "37.0",
                                "shape_pt_lon": "-122.0",
                                "shape_pt_sequence": "1",
                                "shape_dist_traveled": "",
                            },
                        ),
                        request_count=1,
                        cache_hit_count=0,
                        successful_shape_count=1,
                        failure_shape_ids=(),
                        artifacts=(),
                    ),
                ) as mock_backfill,
            ):
                result = extract_sf_historic_archive(
                    metadata_path=metadata_path,
                    acquisitions_root=output_root,
                    api_key="test-token",
                    shapes_cache_root=cache_root,
                    active_metadata_path=source_root / "unused_active_metadata.json",
                )

            shape_rows = _read_member_rows(result.artifact_path, "shapes.txt")
            expected_shape_id = _build_shape_pattern_id(
                selected_agency_id="SF",
                route_id="SF:1",
                direction_id="1",
                trip_headsign="Downtown",
                stop_pattern_key=_stop_pattern_key("1:SF:STOP1"),
            )
            self.assertEqual(len(shape_rows), 1)
            self.assertEqual(shape_rows[0]["shape_id"], expected_shape_id)
            self.assertEqual(
                mock_backfill.call_args.args[0],
                {expected_shape_id: ["SF:TRIP1:20260415", "ACTIVE_TRIP_A", "ACTIVE_TRIP_B"]},
            )
        finally:
            shutil.rmtree(source_root, ignore_errors=True)
            shutil.rmtree(output_root, ignore_errors=True)
            shutil.rmtree(cache_root, ignore_errors=True)

    def test_extract_sf_historic_archive_does_not_merge_blank_shape_id_trips_with_same_headsign(self) -> None:
        workspace_tmp_root = Path(__file__).resolve().parents[2] / ".tmp"
        workspace_tmp_root.mkdir(parents=True, exist_ok=True)
        source_root = workspace_tmp_root / "historic_rg_sf_extract_no_merge_source"
        output_root = workspace_tmp_root / "historic_rg_sf_extract_no_merge_output"
        cache_root = workspace_tmp_root / "historic_rg_sf_extract_no_merge_cache"
        shutil.rmtree(source_root, ignore_errors=True)
        shutil.rmtree(output_root, ignore_errors=True)
        shutil.rmtree(cache_root, ignore_errors=True)
        source_root.mkdir(parents=True, exist_ok=True)
        output_root.mkdir(parents=True, exist_ok=True)
        cache_root.mkdir(parents=True, exist_ok=True)

        try:
            artifact_path = source_root / "511_regional_historic_RG_202604_with_so_test.zip"
            artifact_path.write_bytes(_make_regional_archive_bytes_without_shapes_or_shape_ids_two_trips_same_headsign())
            metadata_path = source_root / "511_regional_historic_RG_202604_with_so_test.json"
            metadata_path.write_text(
                json.dumps(
                    {
                        "source_system": "511",
                        "feed_scope": "regional_historic",
                        "operator_id": "RG",
                        "artifact_filename": artifact_path.name,
                        "requested_historic_month": "2026-04",
                        "requested_historic_value": "2026-04-so",
                        "requested_stop_observations": True,
                        "stop_observations_present": True,
                        "shapes_present": False,
                    },
                    indent=2,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            with patch(
                "muni_lta_pipeline.historic_rg_sf_extract.backfill_missing_shapes",
                return_value=SimpleNamespace(
                    shape_rows=(
                            {
                                "shape_id": _build_shape_pattern_id(
                                    selected_agency_id="SF",
                                    route_id="SF:1",
                                    direction_id="1",
                                    trip_headsign="Downtown",
                                    stop_pattern_key=_stop_pattern_key("1:SF:STOP1", "2:SF:STOP2"),
                                ),
                            "shape_pt_lat": "37.0",
                            "shape_pt_lon": "-122.0",
                            "shape_pt_sequence": "1",
                            "shape_dist_traveled": "",
                        },
                            {
                                "shape_id": _build_shape_pattern_id(
                                    selected_agency_id="SF",
                                    route_id="SF:1",
                                    direction_id="1",
                                    trip_headsign="Downtown",
                                    stop_pattern_key=_stop_pattern_key("1:SF:STOP2", "2:SF:STOP1"),
                                ),
                            "shape_pt_lat": "37.1",
                            "shape_pt_lon": "-122.1",
                            "shape_pt_sequence": "1",
                            "shape_dist_traveled": "",
                        },
                    ),
                    request_count=2,
                    cache_hit_count=0,
                    successful_shape_count=2,
                    failure_shape_ids=(),
                    artifacts=(),
                ),
            ) as mock_backfill:
                result = extract_sf_historic_archive(
                    metadata_path=metadata_path,
                    acquisitions_root=output_root,
                    api_key="test-token",
                    shapes_cache_root=cache_root,
                )

            trip_rows = _read_member_rows(result.artifact_path, "trips.txt")
            expected_shape_id_trip_1 = _build_shape_pattern_id(
                selected_agency_id="SF",
                route_id="SF:1",
                direction_id="1",
                trip_headsign="Downtown",
                stop_pattern_key=_stop_pattern_key("1:SF:STOP1", "2:SF:STOP2"),
            )
            expected_shape_id_trip_2 = _build_shape_pattern_id(
                selected_agency_id="SF",
                route_id="SF:1",
                direction_id="1",
                trip_headsign="Downtown",
                stop_pattern_key=_stop_pattern_key("1:SF:STOP2", "2:SF:STOP1"),
            )
            self.assertEqual(
                [row["shape_id"] for row in trip_rows],
                [expected_shape_id_trip_1, expected_shape_id_trip_2],
            )
            self.assertEqual(
                mock_backfill.call_args.args[0],
                {
                    expected_shape_id_trip_1: ["SF:TRIP1:20260415"],
                    expected_shape_id_trip_2: ["SF:TRIP2:20260415"],
                },
            )
        finally:
            shutil.rmtree(source_root, ignore_errors=True)
            shutil.rmtree(output_root, ignore_errors=True)
            shutil.rmtree(cache_root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
