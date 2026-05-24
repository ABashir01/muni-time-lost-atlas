"""Tests for 511 Shapes API parsing and cache reuse."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import unittest
from unittest.mock import patch


def _configure_src_paths() -> None:
    root = Path(__file__).resolve().parents[2]
    for src_dir in (root / "api" / "src", root / "pipeline" / "src"):
        src_str = str(src_dir)
        if src_str not in sys.path:
            sys.path.insert(0, src_str)


_configure_src_paths()

from muni_lta_pipeline.historic_shapes_api import (  # noqa: E402
    backfill_missing_shapes,
    build_shapes_api_url,
    normalize_trip_id_for_shapes_api,
    parse_shapes_api_positions,
)


class _FakeHttpResponse:
    def __init__(self, payload: str) -> None:
        self._payload = payload.encode("utf-8")

    def __enter__(self) -> "_FakeHttpResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self) -> bytes:
        return self._payload


def _sample_shapes_payload() -> str:
    return json.dumps(
        {
            "Content": {
                "TimetableFrame": {
                    "vehicleJourneys": {
                        "ServiceJourney": {
                            "id": "trip_1",
                            "LinkSequenceProjection": {
                                "LineString": {
                                    "pos": [
                                        "37.1000 -122.1000",
                                        "37.2000 -122.2000",
                                    ]
                                }
                            },
                        }
                    }
                }
            }
        }
    )


class HistoricShapesApiTests(unittest.TestCase):
    def test_build_shapes_api_url_includes_operator_trip_and_json_format(self) -> None:
        url = build_shapes_api_url("token-1", operator_id="SF", trip_id="trip_1")
        self.assertIn("api_key=token-1", url)
        self.assertIn("operator_id=SF", url)
        self.assertIn("trip_id=trip_1", url)
        self.assertIn("format=json", url)

    def test_parse_shapes_api_positions_reads_linestring_positions(self) -> None:
        positions = parse_shapes_api_positions(json.loads(_sample_shapes_payload()))
        self.assertEqual(
            positions,
            (("37.1000", "-122.1000"), ("37.2000", "-122.2000")),
        )

    def test_normalize_trip_id_for_shapes_api_strips_namespace_and_date_suffix(self) -> None:
        self.assertEqual(
            normalize_trip_id_for_shapes_api("SF:11976951_M21:20260430", operator_id="SF"),
            "11976951_M21",
        )
        self.assertEqual(
            normalize_trip_id_for_shapes_api("11976951_M21", operator_id="SF"),
            "11976951_M21",
        )

    def test_backfill_missing_shapes_reuses_cached_shape_artifact(self) -> None:
        workspace_tmp_root = Path(__file__).resolve().parents[2] / ".tmp"
        workspace_tmp_root.mkdir(parents=True, exist_ok=True)
        cache_root = workspace_tmp_root / "historic_shapes_api_cache"
        shutil.rmtree(cache_root, ignore_errors=True)
        cache_root.mkdir(parents=True, exist_ok=True)

        try:
            with patch(
                "muni_lta_pipeline.historic_shapes_api.urlopen",
                return_value=_FakeHttpResponse(_sample_shapes_payload()),
            ) as mock_urlopen:
                first_result = backfill_missing_shapes(
                    {"shape_1": "trip_1"},
                    api_key="token-1",
                    operator_id="SF",
                    cache_root=cache_root,
                )

            self.assertEqual(first_result.request_count, 1)
            self.assertEqual(first_result.cache_hit_count, 0)
            self.assertEqual(first_result.successful_shape_count, 1)
            self.assertEqual(len(first_result.shape_rows), 2)
            self.assertEqual(first_result.shape_rows[0]["shape_pt_sequence"], "1")
            mock_urlopen.assert_called_once()

            with patch("muni_lta_pipeline.historic_shapes_api.urlopen") as mock_cached_urlopen:
                second_result = backfill_missing_shapes(
                    {"shape_1": "trip_1"},
                    api_key="token-1",
                    operator_id="SF",
                    cache_root=cache_root,
                )

            self.assertEqual(second_result.request_count, 0)
            self.assertEqual(second_result.cache_hit_count, 1)
            self.assertEqual(second_result.successful_shape_count, 1)
            mock_cached_urlopen.assert_not_called()
        finally:
            shutil.rmtree(cache_root, ignore_errors=True)

    def test_backfill_missing_shapes_tries_multiple_candidate_trip_ids_until_one_succeeds(self) -> None:
        workspace_tmp_root = Path(__file__).resolve().parents[2] / ".tmp"
        workspace_tmp_root.mkdir(parents=True, exist_ok=True)
        cache_root = workspace_tmp_root / "historic_shapes_api_multi_candidate_cache"
        shutil.rmtree(cache_root, ignore_errors=True)
        cache_root.mkdir(parents=True, exist_ok=True)

        try:
            with patch(
                "muni_lta_pipeline.historic_shapes_api.urlopen",
                side_effect=[
                    _FakeHttpResponse(json.dumps({"Content": {"TimetableFrame": {"vehicleJourneys": {}}}})),
                    _FakeHttpResponse(_sample_shapes_payload()),
                ],
            ) as mock_urlopen:
                result = backfill_missing_shapes(
                    {"shape_1": ["SF:trip_1:20260430", "trip_2"]},
                    api_key="token-1",
                    operator_id="SF",
                    cache_root=cache_root,
                )

            self.assertEqual(result.request_count, 2)
            self.assertEqual(result.successful_shape_count, 1)
            self.assertEqual(result.failure_shape_ids, ())
            self.assertEqual(result.artifacts[0].shapes_api_trip_id, "trip_2")
            self.assertEqual(mock_urlopen.call_count, 2)
        finally:
            shutil.rmtree(cache_root, ignore_errors=True)

    def test_backfill_missing_shapes_reuses_cached_geometry_by_shapes_api_trip_id(self) -> None:
        workspace_tmp_root = Path(__file__).resolve().parents[2] / ".tmp"
        workspace_tmp_root.mkdir(parents=True, exist_ok=True)
        cache_root = workspace_tmp_root / "historic_shapes_api_trip_cache"
        shutil.rmtree(cache_root, ignore_errors=True)
        cache_root.mkdir(parents=True, exist_ok=True)

        try:
            with patch(
                "muni_lta_pipeline.historic_shapes_api.urlopen",
                return_value=_FakeHttpResponse(_sample_shapes_payload()),
            ) as mock_urlopen:
                first_result = backfill_missing_shapes(
                    {"shape_1": "trip_1"},
                    api_key="token-1",
                    operator_id="SF",
                    cache_root=cache_root,
                )

            self.assertEqual(first_result.request_count, 1)
            mock_urlopen.assert_called_once()

            with patch("muni_lta_pipeline.historic_shapes_api.urlopen") as mock_cached_urlopen:
                second_result = backfill_missing_shapes(
                    {"shape_2": ["trip_1", "trip_2"]},
                    api_key="token-1",
                    operator_id="SF",
                    cache_root=cache_root,
                )

            self.assertEqual(second_result.request_count, 0)
            self.assertEqual(second_result.cache_hit_count, 1)
            self.assertEqual(second_result.successful_shape_count, 1)
            self.assertEqual(second_result.artifacts[0].shapes_api_trip_id, "trip_1")
            self.assertEqual(second_result.shape_rows[0]["shape_id"], "shape_2")
            mock_cached_urlopen.assert_not_called()
        finally:
            shutil.rmtree(cache_root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
