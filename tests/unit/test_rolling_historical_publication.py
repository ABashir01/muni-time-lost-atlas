"""Unit tests for rolling historical publication helpers."""

from __future__ import annotations

from datetime import date
from io import BytesIO
from io import TextIOWrapper
import json
from pathlib import Path
import shutil
import sys
import unittest
from unittest.mock import patch
import zipfile
import csv


def _configure_src_paths() -> None:
    root = Path(__file__).resolve().parents[2]
    for src_dir in (root / "api" / "src", root / "pipeline" / "src"):
        src_str = str(src_dir)
        if src_str not in sys.path:
            sys.path.insert(0, src_str)


_configure_src_paths()

from muni_lta_pipeline.historic_rg_feed_fetch import HistoricAvailabilityResult  # noqa: E402
from muni_lta_pipeline.rolling_historical_publication import (  # noqa: E402
    _find_latest_cached_historic_metadata_path,
    advance_rolling_historical_publication,
    bootstrap_rolling_historical_publication,
    build_trailing_publication_months,
    combine_historic_month_archives,
    newest_completed_historic_month,
    _prune_publication_storage,
)


def _make_monthly_archive_bytes(
    *,
    route_long_name: str,
    stop_name: str,
    month_token: str,
) -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, mode="w") as archive:
        archive.writestr(
            "routes.txt",
            "route_id,agency_id,route_short_name,route_long_name\nSF:14,SF,14,"
            f"{route_long_name}\n",
        )
        archive.writestr(
            "trips.txt",
            "route_id,service_id,trip_id,trip_headsign,direction_id,shape_id\n"
            f"SF:14,WKD,SF:TRIP:{month_token}01,Mission,1,SF:shape:{month_token}\n",
        )
        archive.writestr(
            "stops.txt",
            "stop_id,stop_name,stop_lat,stop_lon\nSTOP1,"
            f"{stop_name},37.0,-122.0\n",
        )
        archive.writestr(
            "stop_times.txt",
            "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
            f"SF:TRIP:{month_token}01,08:00:00,08:00:00,STOP1,1\n",
        )
        archive.writestr(
            "shapes.txt",
            "shape_id,shape_pt_lat,shape_pt_lon,shape_pt_sequence\n"
            f"SF:shape:{month_token},37.0,-122.0,1\n",
        )
        archive.writestr(
            "calendar_dates.txt",
            f"service_id,date,exception_type\nWKD,{month_token}01,1\n",
        )
        archive.writestr(
            "stop_observations.txt",
            "service_date,trip_id,route_id,stop_sequence,to_stop_id,observed_arrival_time\n"
            f"{month_token}01,SF:TRIP:{month_token}01,SF:14,1,STOP1,08:01:00\n",
        )
    return buffer.getvalue()


class RollingHistoricalPublicationUnitTests(unittest.TestCase):
    def test_newest_completed_historic_month_and_trailing_window(self) -> None:
        self.assertEqual(
            newest_completed_historic_month(current_date=date(2026, 5, 24)),
            "2026-04",
        )
        self.assertEqual(
            build_trailing_publication_months("2026-04", window_months=3),
            ("2026-02", "2026-03", "2026-04"),
        )

    def test_combine_historic_month_archives_namespaces_month_scoped_ids(self) -> None:
        workspace_tmp_root = Path(__file__).resolve().parents[2] / ".tmp"
        workspace_tmp_root.mkdir(parents=True, exist_ok=True)
        scenario_root = workspace_tmp_root / "rolling_publication_combine"
        shutil.rmtree(scenario_root, ignore_errors=True)
        scenario_root.mkdir(parents=True, exist_ok=True)

        try:
            metadata_paths: list[Path] = []
            for historic_month, route_name, stop_name in (
                ("2026-03", "Mission Older", "Older Stop"),
                ("2026-04", "Mission Newer", "Newer Stop"),
            ):
                month_token = historic_month.replace("-", "")
                artifact_path = scenario_root / f"{month_token}.zip"
                artifact_path.write_bytes(
                    _make_monthly_archive_bytes(
                        route_long_name=route_name,
                        stop_name=stop_name,
                        month_token=month_token,
                    )
                )
                metadata_path = scenario_root / f"{month_token}.json"
                metadata_path.write_text(
                    json.dumps(
                        {
                            "artifact_filename": artifact_path.name,
                            "feed_scope": "regional_historic_sf",
                            "operator_id": "SF",
                            "requested_historic_month": historic_month,
                            "requested_historic_value": f"{historic_month}-so",
                            "requested_stop_observations": True,
                            "source_system": "511",
                            "stop_observations_present": True,
                        },
                        indent=2,
                        sort_keys=True,
                    ),
                    encoding="utf-8",
                )
                metadata_paths.append(metadata_path)

            result = combine_historic_month_archives(
                metadata_paths=metadata_paths,
                combined_acquisitions_root=scenario_root / "combined",
            )

            self.assertEqual(result.publication_months, ("2026-03", "2026-04"))
            self.assertTrue(result.artifact_path.exists())
            self.assertTrue(result.metadata_path.exists())

            with zipfile.ZipFile(result.artifact_path, mode="r") as archive:
                with archive.open("routes.txt", mode="r") as raw_handle:
                    routes = list(
                        csv.DictReader(TextIOWrapper(raw_handle, encoding="utf-8", newline=""))
                    )
                with archive.open("stops.txt", mode="r") as raw_handle:
                    stops = list(
                        csv.DictReader(TextIOWrapper(raw_handle, encoding="utf-8", newline=""))
                    )
                with archive.open("trips.txt", mode="r") as raw_handle:
                    trips = list(
                        csv.DictReader(TextIOWrapper(raw_handle, encoding="utf-8", newline=""))
                    )
                with archive.open("stop_observations.txt", mode="r") as raw_handle:
                    observations = list(
                        csv.DictReader(TextIOWrapper(raw_handle, encoding="utf-8", newline=""))
                    )

            self.assertEqual(routes[0]["route_long_name"], "Mission Newer")
            self.assertEqual(stops[0]["stop_name"], "Newer Stop")
            self.assertEqual(len(trips), 2)
            self.assertTrue(all(row["trip_id"].startswith(("202603__", "202604__")) for row in trips))
            self.assertTrue(
                all(row["trip_id"].startswith(("202603__", "202604__")) for row in observations)
            )
        finally:
            shutil.rmtree(scenario_root, ignore_errors=True)

    def test_bootstrap_rolling_historical_publication_uses_trailing_window(self) -> None:
        availability = HistoricAvailabilityResult(
            historic_month="2026-04",
            include_stop_observations=True,
            requested_url="https://example.test",
            available=True,
            checked_at="2026-05-24T09:00:00+00:00",
            request_method="HEAD",
            status_code=200,
        )
        expected_months = ("2026-02", "2026-03", "2026-04")
        publication_result = {
            "action": "bootstrap",
            "historic_agency_id": "SF",
            "latest_available_month": "2026-04",
            "publication_months": expected_months,
            "publication_manifest_path": Path("publication.json"),
            "latest_publication_manifest_path": Path("latest.json"),
            "active_metadata_path": None,
            "combined_metadata_path": None,
            "cutover_manifest_path": None,
            "availability_status_code": 200,
            "availability_request_method": "bootstrap",
            "published": True,
            "route_count_with_metrics": 68,
            "map_route_count": 68,
            "top_route_ids": ("SF:12", "SF:14"),
        }

        with (
            patch(
                "muni_lta_pipeline.rolling_historical_publication.get_511_api_key",
                return_value="token",
            ),
            patch(
                "muni_lta_pipeline.rolling_historical_publication.check_newest_available_completed_month",
                return_value=availability,
            ),
            patch(
                "muni_lta_pipeline.rolling_historical_publication._publish_month_window",
                return_value=publication_result,
            ) as mock_publish,
        ):
            result = bootstrap_rolling_historical_publication(current_date=date(2026, 5, 24))

        self.assertEqual(result, publication_result)
        self.assertEqual(mock_publish.call_args.kwargs["publication_months"], expected_months)

    def test_bootstrap_rolling_historical_publication_skips_availability_probe_for_explicit_month(self) -> None:
        expected_months = ("2026-02", "2026-03", "2026-04")
        publication_result = {
            "action": "bootstrap",
            "historic_agency_id": "SF",
            "latest_available_month": "2026-04",
            "publication_months": expected_months,
            "publication_manifest_path": Path("publication.json"),
            "latest_publication_manifest_path": Path("latest.json"),
            "active_metadata_path": None,
            "combined_metadata_path": None,
            "cutover_manifest_path": None,
            "availability_status_code": 200,
            "availability_request_method": "manual_override",
            "published": True,
            "route_count_with_metrics": 68,
            "map_route_count": 68,
            "top_route_ids": ("SF:12", "SF:14"),
        }

        with (
            patch(
                "muni_lta_pipeline.rolling_historical_publication.check_historic_rg_gtfs_archive_availability",
                side_effect=AssertionError("explicit month should not probe availability"),
            ),
            patch(
                "muni_lta_pipeline.rolling_historical_publication._publish_month_window",
                return_value=publication_result,
            ) as mock_publish,
        ):
            result = bootstrap_rolling_historical_publication(
                latest_available_month="2026-04"
            )

        self.assertEqual(result, publication_result)
        self.assertEqual(mock_publish.call_args.kwargs["publication_months"], expected_months)
        self.assertEqual(mock_publish.call_args.kwargs["latest_available_month"], "2026-04")

    def test_bootstrap_rolling_historical_publication_reuses_cached_active_metadata(self) -> None:
        workspace_tmp_root = Path(__file__).resolve().parents[2] / ".tmp"
        workspace_tmp_root.mkdir(parents=True, exist_ok=True)
        active_root = workspace_tmp_root / "rolling_publication_active_cache"
        shutil.rmtree(active_root, ignore_errors=True)
        active_root.mkdir(parents=True, exist_ok=True)

        artifact_path = active_root / "511_operator_active_SF_20260601T010203Z.zip"
        artifact_path.write_bytes(b"zip")
        metadata_path = active_root / "511_operator_active_SF_20260601T010203Z.json"
        metadata_path.write_text(
            json.dumps({"artifact_filename": artifact_path.name}, indent=2, sort_keys=True),
            encoding="utf-8",
        )

        expected_months = ("2026-02", "2026-03", "2026-04")
        publication_result = {
            "action": "bootstrap",
            "historic_agency_id": "SF",
            "latest_available_month": "2026-04",
            "publication_months": expected_months,
            "publication_manifest_path": Path("publication.json"),
            "latest_publication_manifest_path": Path("latest.json"),
            "active_metadata_path": metadata_path,
            "combined_metadata_path": None,
            "cutover_manifest_path": None,
            "availability_status_code": 200,
            "availability_request_method": "manual_override",
            "published": True,
            "route_count_with_metrics": 68,
            "map_route_count": 68,
            "top_route_ids": ("SF:12", "SF:14"),
        }

        with (
            patch(
                "muni_lta_pipeline.rolling_historical_publication.fetch_active_gtfs_archive",
                side_effect=AssertionError("cached active metadata should be reused"),
            ),
            patch(
                "muni_lta_pipeline.rolling_historical_publication._publish_month_window",
                return_value=publication_result,
            ) as mock_publish,
        ):
            result = bootstrap_rolling_historical_publication(
                latest_available_month="2026-04",
                active_acquisitions_root=active_root,
            )

        self.assertEqual(result, publication_result)
        self.assertEqual(mock_publish.call_args.kwargs["publication_months"], expected_months)

    def test_bootstrap_rolling_historical_publication_reuses_cached_historic_metadata(self) -> None:
        workspace_tmp_root = Path(__file__).resolve().parents[2] / ".tmp"
        workspace_tmp_root.mkdir(parents=True, exist_ok=True)
        historic_root = workspace_tmp_root / "rolling_publication_historic_cache"
        shutil.rmtree(historic_root, ignore_errors=True)
        historic_root.mkdir(parents=True, exist_ok=True)

        artifact_path = historic_root / "511_regional_historic_RG_202602_with_so_20260601T010203Z.zip"
        artifact_path.write_bytes(b"zip")
        metadata_path = historic_root / "511_regional_historic_RG_202602_with_so_20260601T010203Z.json"
        metadata_path.write_text(
            json.dumps(
                {
                    "artifact_filename": artifact_path.name,
                    "requested_historic_month": "2026-02",
                    "requested_stop_observations": True,
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        self.assertEqual(
            _find_latest_cached_historic_metadata_path(
                historic_root,
                historic_month="2026-02",
                include_stop_observations=True,
            ),
            metadata_path,
        )

    def test_advance_rolling_historical_publication_exits_cleanly_when_latest_month_is_already_published(self) -> None:
        workspace_tmp_root = Path(__file__).resolve().parents[2] / ".tmp"
        workspace_tmp_root.mkdir(parents=True, exist_ok=True)
        publication_root = workspace_tmp_root / "rolling_publication_manifest"
        shutil.rmtree(publication_root, ignore_errors=True)
        publication_root.mkdir(parents=True, exist_ok=True)
        (publication_root / "latest.json").write_text(
            json.dumps(
                {
                    "latest_available_month": "2026-04",
                    "publication_months": [
                        "2026-02",
                        "2026-03",
                        "2026-04",
                    ],
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        availability = HistoricAvailabilityResult(
            historic_month="2026-04",
            include_stop_observations=True,
            requested_url="https://example.test",
            available=True,
            checked_at="2026-05-24T09:00:00+00:00",
            request_method="HEAD",
            status_code=200,
        )

        with (
            patch(
                "muni_lta_pipeline.rolling_historical_publication.get_511_api_key",
                return_value="token",
            ),
            patch(
                "muni_lta_pipeline.rolling_historical_publication.check_newest_available_completed_month",
                return_value=availability,
            ),
        ):
            result = advance_rolling_historical_publication(
                current_date=date(2026, 5, 24),
                publication_root=publication_root,
            )

        self.assertEqual(result.action, "already_published")
        self.assertFalse(result.published)
        self.assertEqual(result.latest_available_month, "2026-04")

    def test_advance_rolling_historical_publication_skips_availability_probe_for_explicit_target_month(self) -> None:
        workspace_tmp_root = Path(__file__).resolve().parents[2] / ".tmp"
        workspace_tmp_root.mkdir(parents=True, exist_ok=True)
        publication_root = workspace_tmp_root / "rolling_publication_manual_target"
        shutil.rmtree(publication_root, ignore_errors=True)
        publication_root.mkdir(parents=True, exist_ok=True)
        (publication_root / "latest.json").write_text(
            json.dumps(
                {
                    "latest_available_month": "2026-03",
                    "publication_months": [
                        "2026-01",
                        "2026-02",
                        "2026-03",
                    ],
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        expected_months = ("2026-02", "2026-03", "2026-04")
        publication_result = {
            "action": "advance",
            "historic_agency_id": "SF",
            "latest_available_month": "2026-04",
            "publication_months": expected_months,
            "publication_manifest_path": Path("publication.json"),
            "latest_publication_manifest_path": Path("latest.json"),
            "active_metadata_path": None,
            "combined_metadata_path": None,
            "cutover_manifest_path": None,
            "availability_status_code": 200,
            "availability_request_method": "manual_override",
            "published": True,
            "route_count_with_metrics": 68,
            "map_route_count": 68,
            "top_route_ids": ("SF:12", "SF:14"),
        }

        with (
            patch(
                "muni_lta_pipeline.rolling_historical_publication.check_historic_rg_gtfs_archive_availability",
                side_effect=AssertionError("explicit target month should not probe availability"),
            ),
            patch(
                "muni_lta_pipeline.rolling_historical_publication._publish_month_window",
                return_value=publication_result,
            ) as mock_publish,
        ):
            result = advance_rolling_historical_publication(
                publication_root=publication_root,
                target_month="2026-04",
            )

        self.assertEqual(result, publication_result)
        self.assertEqual(mock_publish.call_args.kwargs["publication_months"], expected_months)
        self.assertEqual(mock_publish.call_args.kwargs["latest_available_month"], "2026-04")

    def test_prune_publication_storage_keeps_only_current_rolling_artifacts(self) -> None:
        workspace_tmp_root = Path(__file__).resolve().parents[2] / ".tmp"
        workspace_tmp_root.mkdir(parents=True, exist_ok=True)
        scenario_root = workspace_tmp_root / "rolling_publication_prune"
        shutil.rmtree(scenario_root, ignore_errors=True)
        scenario_root.mkdir(parents=True, exist_ok=True)

        active_root = scenario_root / "active"
        historic_root = scenario_root / "historic"
        derived_root = scenario_root / "derived"
        combined_root = scenario_root / "combined"
        publication_root = scenario_root / "publication"
        cutover_root = scenario_root / "cutovers"
        for root in (
            active_root,
            historic_root,
            derived_root,
            combined_root,
            publication_root,
            cutover_root,
        ):
            root.mkdir(parents=True, exist_ok=True)

        def _write_metadata(root: Path, stem: str, *, include_shape_backfill: bool = False) -> Path:
            artifact_path = root / f"{stem}.zip"
            artifact_path.write_bytes(b"zip")
            payload: dict[str, object] = {"artifact_filename": artifact_path.name}
            if include_shape_backfill:
                shape_backfill_manifest = root / f"{stem}_shape_backfill.json"
                shape_backfill_manifest.write_text("{}", encoding="utf-8")
                payload["shape_backfill_manifest_path"] = str(shape_backfill_manifest)
            metadata_path = root / f"{stem}.json"
            metadata_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
            return metadata_path

        active_keep = _write_metadata(active_root, "active_current")
        active_stale = _write_metadata(active_root, "active_old")
        historic_keep = _write_metadata(historic_root, "historic_current")
        historic_stale = _write_metadata(historic_root, "historic_old")
        derived_keep = _write_metadata(derived_root, "derived_current", include_shape_backfill=True)
        derived_stale = _write_metadata(derived_root, "derived_old", include_shape_backfill=True)
        combined_keep = _write_metadata(combined_root, "combined_current")
        combined_stale = _write_metadata(combined_root, "combined_old")

        publication_manifest = publication_root / "20260524T120000Z.json"
        publication_manifest.write_text("{}", encoding="utf-8")
        latest_publication_manifest = publication_root / "latest.json"
        latest_publication_manifest.write_text("{}", encoding="utf-8")
        stale_publication_manifest = publication_root / "20260523T120000Z.json"
        stale_publication_manifest.write_text("{}", encoding="utf-8")

        cutover_manifest = cutover_root / "20260524T120000Z.json"
        cutover_manifest.write_text("{}", encoding="utf-8")
        cutover_log = cutover_root / "20260524T120000Z.log"
        cutover_log.write_text("{}", encoding="utf-8")
        latest_cutover_manifest = cutover_root / "latest.json"
        latest_cutover_manifest.write_text("{}", encoding="utf-8")
        latest_cutover_log = cutover_root / "latest.log"
        latest_cutover_log.write_text("{}", encoding="utf-8")
        stale_cutover_manifest = cutover_root / "20260523T120000Z.json"
        stale_cutover_manifest.write_text("{}", encoding="utf-8")
        stale_cutover_log = cutover_root / "20260523T120000Z.log"
        stale_cutover_log.write_text("{}", encoding="utf-8")

        _prune_publication_storage(
            active_metadata_path=active_keep,
            monthly_metadata_paths=[historic_keep, derived_keep],
            combined_metadata_path=combined_keep,
            publication_manifest_path=publication_manifest,
            latest_publication_manifest_path=latest_publication_manifest,
            cutover_manifest_path=cutover_manifest,
            cutover_latest_manifest_path=latest_cutover_manifest,
            cutover_log_path=cutover_log,
            cutover_latest_log_path=latest_cutover_log,
            active_root=active_root,
            historic_root=historic_root,
            derived_root=derived_root,
            combined_root=combined_root,
            publication_root=publication_root,
            cutover_root=cutover_root,
        )

        self.assertTrue(active_keep.exists())
        self.assertFalse(active_stale.exists())
        self.assertTrue(historic_keep.exists())
        self.assertFalse(historic_stale.exists())
        self.assertTrue(derived_keep.exists())
        self.assertFalse(derived_stale.exists())
        self.assertTrue(combined_keep.exists())
        self.assertFalse(combined_stale.exists())
        self.assertTrue(publication_manifest.exists())
        self.assertTrue(latest_publication_manifest.exists())
        self.assertFalse(stale_publication_manifest.exists())
        self.assertTrue(cutover_manifest.exists())
        self.assertTrue(cutover_log.exists())
        self.assertTrue(latest_cutover_manifest.exists())
        self.assertTrue(latest_cutover_log.exists())
        self.assertFalse(stale_cutover_manifest.exists())
        self.assertFalse(stale_cutover_log.exists())


if __name__ == "__main__":
    unittest.main()
