"""Unit tests for GTFS-RT live vehicle ingest helpers."""

from __future__ import annotations

from datetime import UTC, datetime
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

from google.transit import gtfs_realtime_pb2  # noqa: E402

from muni_lta_pipeline.live_vehicle_positions_ingest import (  # noqa: E402
    DEFAULT_AGENCY_ID,
    build_vehicle_positions_url,
    parse_vehicle_positions_feed,
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
    second.id = "mystery-bus"
    second.vehicle.vehicle.id = "mystery-bus"
    second.vehicle.position.latitude = 37.79
    second.vehicle.position.longitude = -122.41
    second.vehicle.current_status = gtfs_realtime_pb2.VehiclePosition.STOPPED_AT
    second.vehicle.timestamp = 1779525954

    return feed.SerializeToString()


class LiveVehiclePositionsIngestUnitTests(unittest.TestCase):
    def test_build_vehicle_positions_url_targets_511_vehicle_positions_endpoint(self) -> None:
        url = build_vehicle_positions_url("test-key", agency_id="SF")
        self.assertEqual(
            url,
            "https://api.511.org/transit/vehiclepositions?api_key=test-key&agency=SF",
        )

    def test_parse_vehicle_positions_feed_normalizes_route_ids_and_optional_fields(self) -> None:
        fetched_at = datetime(2026, 5, 23, 18, 45, 0, tzinfo=UTC)
        feed_timestamp, records = parse_vehicle_positions_feed(
            _build_feed_payload(),
            agency_id=DEFAULT_AGENCY_ID,
            fetched_at=fetched_at,
        )

        self.assertEqual(feed_timestamp, datetime(2026, 5, 23, 8, 45, 57, tzinfo=UTC))
        self.assertEqual(len(records), 2)

        first = records[0]
        self.assertEqual(first.entity_id, "5743")
        self.assertEqual(first.route_id, "SF:14")
        self.assertEqual(first.route_short_name, "14")
        self.assertEqual(first.trip_id, "11996409_M11")
        self.assertEqual(first.current_status, "IN_TRANSIT_TO")
        self.assertEqual(first.stop_id, "15541")
        self.assertEqual(first.current_stop_sequence, 16)
        self.assertAlmostEqual(first.latitude, 37.7756958, places=6)
        self.assertAlmostEqual(first.longitude, -122.4153747, places=6)
        self.assertEqual(first.vehicle_timestamp, datetime(2026, 5, 23, 8, 45, 55, tzinfo=UTC))

        second = records[1]
        self.assertEqual(second.entity_id, "mystery-bus")
        self.assertIsNone(second.route_id)
        self.assertIsNone(second.route_short_name)
        self.assertEqual(second.current_status, "STOPPED_AT")


if __name__ == "__main__":
    unittest.main()
