"""Tests for active 511 GTFS acquisition helpers."""

from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
import shutil
import sys
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

from muni_lta_pipeline.active_gtfs_fetch import (  # noqa: E402
    CORE_GTFS_FILES,
    DEFAULT_OPERATOR_ID,
    build_active_gtfs_url,
    fetch_active_gtfs_archive,
    get_511_api_key,
    validate_gtfs_zip_bytes,
)


def _make_gtfs_zip_bytes(*, include_calendar: bool = True) -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, mode="w") as archive:
        archive.writestr("routes.txt", "route_id,route_short_name\n1,1\n")
        archive.writestr("trips.txt", "route_id,service_id,trip_id\n1,WKD,TRIP1\n")
        archive.writestr("stops.txt", "stop_id,stop_name\nSTOP1,Stop 1\n")
        archive.writestr(
            "stop_times.txt",
            "trip_id,arrival_time,departure_time,stop_id,stop_sequence\nTRIP1,08:00:00,08:00:00,STOP1,1\n",
        )
        archive.writestr(
            "shapes.txt",
            "shape_id,shape_pt_lat,shape_pt_lon,shape_pt_sequence\nSHAPE1,37.0,-122.0,1\n",
        )
        if include_calendar:
            archive.writestr(
                "calendar.txt",
                "service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\nWKD,1,1,1,1,1,0,0,20260501,20260531\n",
            )
        else:
            archive.writestr(
                "calendar_dates.txt",
                "service_id,date,exception_type\nWKD,20260501,1\n",
            )
    return buffer.getvalue()


class _FakeHttpResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def __enter__(self) -> "_FakeHttpResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self) -> bytes:
        return self._payload


class ActiveGtfsFetchTests(unittest.TestCase):
    def test_build_active_gtfs_url_uses_operator_specific_feed(self) -> None:
        url = build_active_gtfs_url("abc123", operator_id=DEFAULT_OPERATOR_ID)
        self.assertIn("api_key=abc123", url)
        self.assertIn("operator_id=SF", url)
        self.assertTrue(url.startswith("https://api.511.org/transit/datafeeds?"))

    def test_validate_gtfs_zip_bytes_accepts_core_files_with_service_calendar(self) -> None:
        member_names, service_files_present = validate_gtfs_zip_bytes(
            _make_gtfs_zip_bytes(include_calendar=False)
        )

        self.assertTrue(set(CORE_GTFS_FILES).issubset(set(member_names)))
        self.assertEqual(service_files_present, ("calendar_dates.txt",))

    def test_get_511_api_key_uses_local_env_mapping(self) -> None:
        api_key = get_511_api_key({"TRANSIT_511_API_KEY": "test-token"})
        self.assertEqual(api_key, "test-token")

    def test_fetch_active_gtfs_archive_writes_zip_and_metadata(self) -> None:
        payload = _make_gtfs_zip_bytes()
        workspace_tmp_root = Path(__file__).resolve().parents[2] / ".tmp"
        workspace_tmp_root.mkdir(parents=True, exist_ok=True)
        acquisitions_root = workspace_tmp_root / "active_gtfs_fetch_test"
        shutil.rmtree(acquisitions_root, ignore_errors=True)
        acquisitions_root.mkdir(parents=True, exist_ok=True)
        try:
            with patch(
                "muni_lta_pipeline.active_gtfs_fetch.urlopen",
                return_value=_FakeHttpResponse(payload),
            ) as mock_urlopen:
                result = fetch_active_gtfs_archive(
                    api_key="test-token",
                    acquisitions_root=acquisitions_root,
                )

            self.assertTrue(result.artifact_path.exists())
            self.assertTrue(result.metadata_path.exists())
            self.assertEqual(result.artifact_path.read_bytes(), payload)

            metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
            self.assertEqual(metadata["source_system"], "511")
            self.assertEqual(metadata["feed_scope"], "operator_active")
            self.assertEqual(metadata["operator_id"], "SF")
            self.assertIn("operator_id=SF", metadata["requested_url"])
            self.assertTrue(set(CORE_GTFS_FILES).issubset(set(metadata["zip_member_names"])))
            self.assertEqual(metadata["service_files_present"], ["calendar.txt"])
            mock_urlopen.assert_called_once()
        finally:
            shutil.rmtree(acquisitions_root, ignore_errors=True)
