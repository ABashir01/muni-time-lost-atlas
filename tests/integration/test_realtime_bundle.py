"""Integration tests for the B7 realtime ingest and live vehicle API surface."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

from fastapi.testclient import TestClient
from google.transit import gtfs_realtime_pb2


def _configure_src_paths() -> None:
    root = Path(__file__).resolve().parents[2]
    for src_dir in (root / "api" / "src", root / "pipeline" / "src"):
        src_str = str(src_dir)
        if src_str not in sys.path:
            sys.path.insert(0, src_str)


_configure_src_paths()

from muni_lta_api.app import create_app  # noqa: E402
from muni_lta_pipeline.active_gtfs_fetch import get_511_api_key  # noqa: E402
from muni_lta_pipeline.live_vehicle_positions_ingest import (  # noqa: E402
    DEFAULT_AGENCY_ID,
    load_live_vehicle_positions,
)


def _build_feed_payload() -> bytes:
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.header.gtfs_realtime_version = "2.0"
    feed.header.timestamp = 1779525957

    first = feed.entity.add()
    first.id = "5743"
    first.vehicle.vehicle.id = "5743"
    first.vehicle.vehicle.label = "5743"
    first.vehicle.trip.trip_id = "11996409_M11"
    first.vehicle.trip.route_id = "14"
    first.vehicle.stop_id = "15541"
    first.vehicle.current_stop_sequence = 16
    first.vehicle.current_status = gtfs_realtime_pb2.VehiclePosition.IN_TRANSIT_TO
    first.vehicle.position.latitude = 37.7756958
    first.vehicle.position.longitude = -122.4153747
    first.vehicle.position.bearing = 45
    first.vehicle.position.speed = 7.8
    first.vehicle.timestamp = 1779525955

    second = feed.entity.add()
    second.id = "5818"
    second.vehicle.vehicle.id = "5818"
    second.vehicle.vehicle.label = "5818"
    second.vehicle.trip.trip_id = "11999801_M11"
    second.vehicle.trip.route_id = "49"
    second.vehicle.stop_id = "14710"
    second.vehicle.current_stop_sequence = 4
    second.vehicle.current_status = gtfs_realtime_pb2.VehiclePosition.INCOMING_AT
    second.vehicle.position.latitude = 37.7932
    second.vehicle.position.longitude = -122.4074
    second.vehicle.position.bearing = 180
    second.vehicle.position.speed = 4.2
    second.vehicle.timestamp = 1779525954

    return feed.SerializeToString()


class RealtimeBundleIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(create_app())

    def setUp(self) -> None:
        self.seed_result = load_live_vehicle_positions(payload=_build_feed_payload())

    def test_live_vehicle_ingest_and_endpoint_publish_current_snapshot(self) -> None:
        self.assertEqual(self.seed_result.inserted_row_count, 2)
        self.assertEqual(self.seed_result.route_ids_with_live_vehicles, ["SF:14", "SF:49"])

        response = self.client.get("/live/vehicles", params={"agency": DEFAULT_AGENCY_ID})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["agency_id"], "SF")
        self.assertEqual(payload["vehicle_count"], 2)
        self.assertEqual(payload["type"], "FeatureCollection")
        self.assertEqual(len(payload["features"]), 2)
        self.assertEqual(payload["features"][0]["geometry"]["type"], "Point")
        self.assertEqual(payload["features"][0]["properties"]["route_id"], "SF:14")
        self.assertEqual(payload["features"][0]["properties"]["route_short_name"], "14")

        filtered_response = self.client.get(
            "/live/vehicles",
            params={"agency": DEFAULT_AGENCY_ID, "route_id": "SF:14"},
        )
        self.assertEqual(filtered_response.status_code, 200)
        filtered_payload = filtered_response.json()
        self.assertEqual(filtered_payload["vehicle_count"], 1)
        self.assertEqual(filtered_payload["route_id"], "SF:14")
        self.assertEqual(
            filtered_payload["features"][0]["properties"]["vehicle_id"],
            "5743",
        )

    def test_live_511_vehicle_positions_fetch_verification(self) -> None:
        try:
            api_key = get_511_api_key()
        except ValueError as exc:
            raise unittest.SkipTest(str(exc)) from exc

        if api_key == "replace_with_local_511_token":
            raise unittest.SkipTest(
                "TRANSIT_511_API_KEY is still the placeholder example value."
            )

        result = load_live_vehicle_positions(api_key=api_key)
        self.assertGreater(result.inserted_row_count, 0)
        self.assertTrue(result.route_short_names_with_live_vehicles)


if __name__ == "__main__":
    unittest.main()
