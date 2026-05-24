"""Tests for historic 511 regional GTFS acquisition helpers."""

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

from muni_lta_pipeline.historic_rg_feed_fetch import (  # noqa: E402
    HISTORIC_REQUIRED_CORE_FILES,
    DEFAULT_OPERATOR_ID,
    STOP_OBSERVATIONS_FILENAME,
    build_historic_rg_gtfs_url,
    fetch_historic_rg_gtfs_archive,
    validate_historic_gtfs_zip_bytes,
    validate_historic_month,
)


def _make_gtfs_zip_bytes(
    *,
    include_shapes: bool = True,
    include_stop_observations: bool = False,
) -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, mode="w") as archive:
        archive.writestr("routes.txt", "route_id,route_short_name\n1,1\n")
        archive.writestr("trips.txt", "route_id,service_id,trip_id\n1,WKD,TRIP1\n")
        archive.writestr("stops.txt", "stop_id,stop_name\nSTOP1,Stop 1\n")
        archive.writestr(
            "stop_times.txt",
            "trip_id,arrival_time,departure_time,stop_id,stop_sequence\nTRIP1,08:00:00,08:00:00,STOP1,1\n",
        )
        if include_shapes:
            archive.writestr(
                "shapes.txt",
                "shape_id,shape_pt_lat,shape_pt_lon,shape_pt_sequence\nSHAPE1,37.0,-122.0,1\n",
            )
        archive.writestr(
            "calendar_dates.txt",
            "service_id,date,exception_type\nWKD,20260501,1\n",
        )
        if include_stop_observations:
            archive.writestr(
                STOP_OBSERVATIONS_FILENAME,
                "trip_id,stop_id,observed_arrival_time\nTRIP1,STOP1,08:01:00\n",
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


class HistoricRgGtfsFetchTests(unittest.TestCase):
    def test_validate_historic_month_normalizes_valid_value(self) -> None:
        self.assertEqual(validate_historic_month("2023-02"), "2023-02")

    def test_build_historic_rg_gtfs_url_supports_plain_and_so_variants(self) -> None:
        plain_url = build_historic_rg_gtfs_url(
            "abc123",
            historic_month="2023-02",
            include_stop_observations=False,
        )
        so_url = build_historic_rg_gtfs_url(
            "abc123",
            historic_month="2023-02",
            include_stop_observations=True,
        )

        self.assertIn("api_key=abc123", plain_url)
        self.assertIn("operator_id=RG", plain_url)
        self.assertIn("historic=2023-02", plain_url)
        self.assertNotIn("historic=2023-02-so", plain_url)
        self.assertIn("historic=2023-02-so", so_url)
        self.assertTrue(plain_url.startswith("https://api.511.org/transit/datafeeds?"))

    def test_validate_historic_gtfs_zip_bytes_enforces_stop_observations_variant(self) -> None:
        plain_member_names, service_files_present, shapes_present, stop_obs_present = (
            validate_historic_gtfs_zip_bytes(
                _make_gtfs_zip_bytes(include_stop_observations=False),
                require_stop_observations=False,
            )
        )
        self.assertTrue(set(HISTORIC_REQUIRED_CORE_FILES).issubset(set(plain_member_names)))
        self.assertEqual(service_files_present, ("calendar_dates.txt",))
        self.assertTrue(shapes_present)
        self.assertFalse(stop_obs_present)

        missing_shapes_member_names, _, missing_shapes_present, _ = validate_historic_gtfs_zip_bytes(
            _make_gtfs_zip_bytes(include_shapes=False, include_stop_observations=False),
            require_stop_observations=False,
        )
        self.assertTrue(set(HISTORIC_REQUIRED_CORE_FILES).issubset(set(missing_shapes_member_names)))
        self.assertFalse(missing_shapes_present)

        with self.assertRaisesRegex(ValueError, "missing stop_observations.txt"):
            validate_historic_gtfs_zip_bytes(
                _make_gtfs_zip_bytes(include_stop_observations=False),
                require_stop_observations=True,
            )

        with self.assertRaisesRegex(ValueError, "unexpectedly contains stop_observations.txt"):
            validate_historic_gtfs_zip_bytes(
                _make_gtfs_zip_bytes(include_stop_observations=True),
                require_stop_observations=False,
            )

    def test_fetch_historic_rg_gtfs_archive_writes_plain_metadata(self) -> None:
        payload = _make_gtfs_zip_bytes(include_stop_observations=False)
        workspace_tmp_root = Path(__file__).resolve().parents[2] / ".tmp"
        workspace_tmp_root.mkdir(parents=True, exist_ok=True)
        acquisitions_root = workspace_tmp_root / "historic_rg_fetch_plain_test"
        shutil.rmtree(acquisitions_root, ignore_errors=True)
        acquisitions_root.mkdir(parents=True, exist_ok=True)
        try:
            with patch(
                "muni_lta_pipeline.historic_rg_feed_fetch.urlopen",
                return_value=_FakeHttpResponse(payload),
            ) as mock_urlopen:
                result = fetch_historic_rg_gtfs_archive(
                    api_key="test-token",
                    historic_month="2023-02",
                    acquisitions_root=acquisitions_root,
                )

            self.assertTrue(result.artifact_path.exists())
            self.assertTrue(result.metadata_path.exists())
            metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
            self.assertEqual(metadata["source_system"], "511")
            self.assertEqual(metadata["feed_scope"], "regional_historic")
            self.assertEqual(metadata["operator_id"], DEFAULT_OPERATOR_ID)
            self.assertEqual(metadata["requested_historic_month"], "2023-02")
            self.assertEqual(metadata["requested_historic_value"], "2023-02")
            self.assertFalse(metadata["requested_stop_observations"])
            self.assertTrue(metadata["shapes_present"])
            self.assertFalse(metadata["stop_observations_present"])
            self.assertIn("historic=2023-02", metadata["requested_url"])
            self.assertNotIn("historic=2023-02-so", metadata["requested_url"])
            mock_urlopen.assert_called_once()
        finally:
            shutil.rmtree(acquisitions_root, ignore_errors=True)

    def test_fetch_historic_rg_gtfs_archive_allows_missing_shapes_for_recent_build_fallback(self) -> None:
        payload = _make_gtfs_zip_bytes(include_shapes=False, include_stop_observations=True)
        workspace_tmp_root = Path(__file__).resolve().parents[2] / ".tmp"
        workspace_tmp_root.mkdir(parents=True, exist_ok=True)
        acquisitions_root = workspace_tmp_root / "historic_rg_fetch_missing_shapes_test"
        shutil.rmtree(acquisitions_root, ignore_errors=True)
        acquisitions_root.mkdir(parents=True, exist_ok=True)
        try:
            with patch(
                "muni_lta_pipeline.historic_rg_feed_fetch.urlopen",
                return_value=_FakeHttpResponse(payload),
            ):
                result = fetch_historic_rg_gtfs_archive(
                    api_key="test-token",
                    historic_month="2026-04",
                    include_stop_observations=True,
                    acquisitions_root=acquisitions_root,
                )

            metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
            self.assertFalse(metadata["shapes_present"])
            self.assertTrue(metadata["stop_observations_present"])
            self.assertNotIn("shapes.txt", metadata["zip_member_names"])
        finally:
            shutil.rmtree(acquisitions_root, ignore_errors=True)

    def test_fetch_historic_rg_gtfs_archive_writes_so_metadata(self) -> None:
        payload = _make_gtfs_zip_bytes(include_stop_observations=True)
        workspace_tmp_root = Path(__file__).resolve().parents[2] / ".tmp"
        workspace_tmp_root.mkdir(parents=True, exist_ok=True)
        acquisitions_root = workspace_tmp_root / "historic_rg_fetch_so_test"
        shutil.rmtree(acquisitions_root, ignore_errors=True)
        acquisitions_root.mkdir(parents=True, exist_ok=True)
        try:
            with patch(
                "muni_lta_pipeline.historic_rg_feed_fetch.urlopen",
                return_value=_FakeHttpResponse(payload),
            ):
                result = fetch_historic_rg_gtfs_archive(
                    api_key="test-token",
                    historic_month="2023-02",
                    include_stop_observations=True,
                    acquisitions_root=acquisitions_root,
                )

            metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
            self.assertEqual(metadata["requested_historic_value"], "2023-02-so")
            self.assertTrue(metadata["requested_stop_observations"])
            self.assertTrue(metadata["stop_observations_present"])
            self.assertIn("historic=2023-02-so", metadata["requested_url"])
            self.assertIn("with_so", metadata["artifact_filename"])
        finally:
            shutil.rmtree(acquisitions_root, ignore_errors=True)
