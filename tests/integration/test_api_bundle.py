"""Integration tests for the B4 historical/static API bundle."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

from fastapi.testclient import TestClient


def _configure_src_paths() -> None:
    root = Path(__file__).resolve().parents[2]
    for src_dir in (root / "api" / "src", root / "pipeline" / "src"):
        src_str = str(src_dir)
        if src_str not in sys.path:
            sys.path.insert(0, src_str)


_configure_src_paths()

from muni_lta_api.app import create_app  # noqa: E402
from muni_lta_pipeline.canonical_observed_stop_events import (  # noqa: E402
    materialize_canonical_observed_stop_events,
)
from muni_lta_pipeline.canonical_scheduled_models import (  # noqa: E402
    materialize_canonical_scheduled_models,
)
from muni_lta_pipeline.gis_segment_metrics import (  # noqa: E402
    materialize_gis_segment_metrics,
)
from muni_lta_pipeline.gtfs_static_fixture_ingest import (  # noqa: E402
    load_gtfs_static_fixture,
)
from muni_lta_pipeline.historic_stop_observations_fixture_ingest import (  # noqa: E402
    load_historic_stop_observations_fixture,
)
from muni_lta_pipeline.transit_lane_overlay_fixture_ingest import (  # noqa: E402
    DEFAULT_FIXTURE_PATH as OVERLAY_FIXTURE_PATH,
    load_transit_lane_overlay_fixture,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
GTFS_FIXTURE_DIR = REPO_ROOT / "fixtures" / "gtfs_static" / "api_bundle"
OBSERVATION_FIXTURE_DIR = (
    REPO_ROOT / "fixtures" / "stop_observations" / "regional_rg_api_bundle"
)


class ApiBundleIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        load_gtfs_static_fixture(
            fixture_dir=GTFS_FIXTURE_DIR,
            snapshot_label="fixture_api_bundle_v1",
        )
        materialize_canonical_scheduled_models()
        load_historic_stop_observations_fixture(
            fixture_dir=OBSERVATION_FIXTURE_DIR,
            snapshot_label="historic_2026_05_so_api_bundle_v1",
        )
        materialize_canonical_observed_stop_events()
        load_transit_lane_overlay_fixture(
            fixture_path=OVERLAY_FIXTURE_PATH,
            snapshot_label="fixture_transit_lanes_v1",
        )
        materialize_gis_segment_metrics()
        cls.client = TestClient(create_app())

    def test_health_endpoint_returns_basic_service_metadata(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "ok",
                "app_name": "Muni Lost Time Atlas API",
                "environment": "development",
            },
        )

    def test_rankings_compare_and_map_endpoints_share_route_level_contracts(self) -> None:
        rankings_response = self.client.get(
            "/rankings",
            params={"window": "all_day", "metric": "typical_trip_loss_minutes"},
        )
        self.assertEqual(rankings_response.status_code, 200)
        rankings_payload = rankings_response.json()
        self.assertEqual(rankings_payload["window"], "all_day")
        self.assertEqual(rankings_payload["metric"], "typical_trip_loss_minutes")
        self.assertEqual(rankings_payload["mode"], "routes")
        self.assertEqual(
            [route["route_id"] for route in rankings_payload["routes"]],
            ["14", "49"],
        )
        self.assertEqual(rankings_payload["routes"][0]["rank"], 1)
        self.assertEqual(rankings_payload["routes"][0]["worst_time_band"], "09:00-09:59")
        self.assertAlmostEqual(
            rankings_payload["routes"][0]["typical_trip_loss_minutes"],
            2.329804,
            places=6,
        )
        self.assertEqual(rankings_payload["routes"][1]["worst_time_band"], "07:00-07:59")
        self.assertAlmostEqual(
            rankings_payload["routes"][1]["typical_trip_loss_minutes"],
            1.041667,
            places=6,
        )

        compare_response = self.client.get(
            "/routes/compare",
            params={"ids": "49,14", "window": "all_day"},
        )
        self.assertEqual(compare_response.status_code, 200)
        compare_payload = compare_response.json()
        self.assertEqual(compare_payload["route_ids"], ["49", "14"])
        self.assertEqual(
            [route["route_id"] for route in compare_payload["routes"]],
            ["49", "14"],
        )
        self.assertEqual(
            compare_payload["routes"][0]["worst_segment_label"],
            "Civic Center -> North Point Van Ness",
        )
        self.assertEqual(
            compare_payload["routes"][1]["worst_stop_wait_label"],
            "8th St Market (Outbound)",
        )

        map_response = self.client.get(
            "/map/routes",
            params={"window": "all_day", "metric": "waiting_loss_minutes"},
        )
        self.assertEqual(map_response.status_code, 200)
        map_payload = map_response.json()
        self.assertEqual(map_payload["type"], "FeatureCollection")
        self.assertEqual(map_payload["metric"], "waiting_loss_minutes")
        self.assertEqual(len(map_payload["features"]), 2)
        self.assertEqual(map_payload["features"][0]["geometry"]["type"], "LineString")
        self.assertEqual(
            map_payload["features"][0]["properties"]["route_id"],
            "14",
        )
        self.assertAlmostEqual(
            map_payload["features"][0]["properties"]["metric_value"],
            0.829804,
            places=6,
        )
        self.assertEqual(
            map_payload["features"][1]["properties"]["route_id"],
            "49",
        )
        self.assertAlmostEqual(
            map_payload["features"][1]["properties"]["metric_value"],
            0.041667,
            places=6,
        )

    def test_route_summary_and_segments_endpoints_return_detail_shapes(self) -> None:
        route_summary_response = self.client.get(
            "/routes/14/summary",
            params={"window": "all_day"},
        )
        self.assertEqual(route_summary_response.status_code, 200)
        route_summary_payload = route_summary_response.json()
        self.assertEqual(route_summary_payload["route_id"], "14")
        self.assertNotIn("direction_id", route_summary_payload)
        self.assertEqual(route_summary_payload["worst_time_band"], "09:00-09:59")
        self.assertEqual(
            route_summary_payload["worst_segment_label"],
            "16th St Mission -> 24th St Mission",
        )

        direction_summary_response = self.client.get(
            "/routes/14/summary",
            params={"window": "all_day", "direction": 1},
        )
        self.assertEqual(direction_summary_response.status_code, 200)
        direction_summary_payload = direction_summary_response.json()
        self.assertEqual(direction_summary_payload["direction_id"], 1)
        self.assertEqual(direction_summary_payload["direction_label"], "Outbound")
        self.assertEqual(direction_summary_payload["worst_time_band"], "09:00-09:59")
        self.assertAlmostEqual(
            direction_summary_payload["typical_trip_loss_minutes"],
            3.5,
            places=6,
        )

        segments_response = self.client.get(
            "/routes/14/segments",
            params={"window": "all_day", "direction": 1},
        )
        self.assertEqual(segments_response.status_code, 200)
        segments_payload = segments_response.json()
        self.assertEqual(segments_payload["type"], "FeatureCollection")
        self.assertEqual(segments_payload["direction_id"], 1)
        self.assertEqual(len(segments_payload["features"]), 2)
        self.assertEqual(
            segments_payload["features"][1]["properties"]["segment_label"],
            "16th St Mission -> 24th St Mission",
        )
        self.assertAlmostEqual(
            segments_payload["features"][1]["properties"][
                "segment_in_vehicle_loss_minutes"
            ],
            2.0,
            places=6,
        )

    def test_validation_and_not_found_paths_stay_narrow(self) -> None:
        invalid_metric_response = self.client.get(
            "/rankings",
            params={"metric": "bunching_rate"},
        )
        self.assertEqual(invalid_metric_response.status_code, 422)

        invalid_compare_response = self.client.get(
            "/routes/compare",
            params={"ids": "14"},
        )
        self.assertEqual(invalid_compare_response.status_code, 422)
        self.assertEqual(
            invalid_compare_response.json()["detail"],
            "ids must contain between 2 and 4 route ids",
        )

        missing_route_response = self.client.get("/routes/999/summary")
        self.assertEqual(missing_route_response.status_code, 404)
        self.assertEqual(
            missing_route_response.json()["detail"],
            "No summary found for route_id=999",
        )

        missing_segments_response = self.client.get(
            "/routes/49/segments",
            params={"direction": 1},
        )
        self.assertEqual(missing_segments_response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
