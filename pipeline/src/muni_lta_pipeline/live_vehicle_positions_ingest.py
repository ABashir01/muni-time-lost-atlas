"""Fetch and load the current 511 GTFS-RT vehicle positions snapshot for Muni."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import psycopg
from google.transit import gtfs_realtime_pb2

from muni_lta_pipeline.active_gtfs_fetch import (
    DEFAULT_SOURCE_SYSTEM,
    get_511_api_key,
)
from muni_lta_pipeline.gtfs_static_fixture_ingest import build_postgres_connection_url
from muni_lta_pipeline.gtfs_static_fixture_ingest import (
    ensure_db_service,
    get_postgres_settings,
    wait_for_database,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DDL_FILE = REPO_ROOT / "db" / "sql" / "07-create-realtime-vehicle-positions-table.sql"
DEFAULT_511_VEHICLE_POSITIONS_URL = "https://api.511.org/transit/vehiclepositions"
DEFAULT_AGENCY_ID = "SF"
DEFAULT_FEED_SCOPE = "gtfs_rt_vehicle_positions"


@dataclass(frozen=True)
class LiveVehiclePositionRecord:
    agency_id: str
    bearing: float | None
    current_status: str | None
    current_stop_sequence: int | None
    entity_id: str
    feed_scope: str
    feed_timestamp: datetime | None
    fetched_at: datetime
    latitude: float
    longitude: float
    occupancy_status: str | None
    route_id: str | None
    route_short_name: str | None
    source_system: str
    speed_meters_per_second: float | None
    stop_id: str | None
    trip_id: str | None
    vehicle_id: str | None
    vehicle_label: str | None
    vehicle_timestamp: datetime | None


@dataclass(frozen=True)
class LiveVehicleIngestResult:
    agency_id: str
    fetched_at: str
    feed_timestamp: str | None
    inserted_row_count: int
    route_ids_with_live_vehicles: list[str]
    route_short_names_with_live_vehicles: list[str]
    source_system: str


def build_vehicle_positions_url(
    api_key: str,
    *,
    agency_id: str = DEFAULT_AGENCY_ID,
    base_url: str = DEFAULT_511_VEHICLE_POSITIONS_URL,
) -> str:
    query = urlencode({"api_key": api_key, "agency": agency_id})
    return f"{base_url}?{query}"


def _normalize_route_id(route_id: str, agency_id: str) -> str | None:
    normalized = route_id.strip()
    if not normalized:
        return None
    if ":" in normalized:
        return normalized
    return f"{agency_id}:{normalized}"


def _route_short_name_from_feed(route_id: str) -> str | None:
    normalized = route_id.strip()
    return normalized or None


def _optional_float(container: Any, field_name: str) -> float | None:
    return float(getattr(container, field_name)) if container.HasField(field_name) else None


def _optional_int(container: Any, field_name: str) -> int | None:
    return int(getattr(container, field_name)) if container.HasField(field_name) else None


def _optional_timestamp(value: int | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromtimestamp(int(value), tz=UTC)


def _enum_name(enum_type: Any, value: int | None) -> str | None:
    if value is None:
        return None
    try:
        return str(enum_type.Name(value))
    except ValueError:
        return None


def fetch_vehicle_positions_bytes(
    *,
    api_key: str,
    agency_id: str = DEFAULT_AGENCY_ID,
    base_url: str = DEFAULT_511_VEHICLE_POSITIONS_URL,
    timeout_seconds: int = 30,
) -> bytes:
    request = Request(
        build_vehicle_positions_url(
            api_key,
            agency_id=agency_id,
            base_url=base_url,
        ),
        headers={"User-Agent": "muni-lost-time-atlas/0.1"},
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        return response.read()


def parse_vehicle_positions_feed(
    payload: bytes,
    *,
    agency_id: str = DEFAULT_AGENCY_ID,
    source_system: str = DEFAULT_SOURCE_SYSTEM,
    feed_scope: str = DEFAULT_FEED_SCOPE,
    fetched_at: datetime | None = None,
) -> tuple[datetime | None, list[LiveVehiclePositionRecord]]:
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(payload)

    effective_fetched_at = fetched_at or datetime.now(tz=UTC)
    feed_timestamp = _optional_timestamp(feed.header.timestamp or None)
    records: list[LiveVehiclePositionRecord] = []

    for entity in feed.entity:
        if not entity.HasField("vehicle"):
            continue

        vehicle = entity.vehicle
        if not vehicle.HasField("position"):
            continue

        latitude = float(vehicle.position.latitude)
        longitude = float(vehicle.position.longitude)
        entity_id = entity.id.strip() or vehicle.vehicle.id.strip() or vehicle.vehicle.label.strip()
        if not entity_id:
            continue

        trip = vehicle.trip if vehicle.HasField("trip") else None
        route_id = _normalize_route_id(trip.route_id if trip is not None else "", agency_id)
        route_short_name = _route_short_name_from_feed(trip.route_id if trip is not None else "")
        current_status = _enum_name(
            gtfs_realtime_pb2.VehiclePosition.VehicleStopStatus,
            _optional_int(vehicle, "current_status"),
        )
        occupancy_status = _enum_name(
            gtfs_realtime_pb2.VehiclePosition.OccupancyStatus,
            _optional_int(vehicle, "occupancy_status"),
        )
        vehicle_timestamp = _optional_timestamp(vehicle.timestamp if vehicle.timestamp else None)

        records.append(
            LiveVehiclePositionRecord(
                agency_id=agency_id,
                bearing=_optional_float(vehicle.position, "bearing"),
                current_status=current_status,
                current_stop_sequence=_optional_int(vehicle, "current_stop_sequence"),
                entity_id=entity_id,
                feed_scope=feed_scope,
                feed_timestamp=feed_timestamp,
                fetched_at=effective_fetched_at,
                latitude=latitude,
                longitude=longitude,
                occupancy_status=occupancy_status,
                route_id=route_id,
                route_short_name=route_short_name,
                source_system=source_system,
                speed_meters_per_second=_optional_float(vehicle.position, "speed"),
                stop_id=vehicle.stop_id.strip() or None,
                trip_id=trip.trip_id.strip() or None if trip is not None else None,
                vehicle_id=vehicle.vehicle.id.strip() or None,
                vehicle_label=vehicle.vehicle.label.strip() or None,
                vehicle_timestamp=vehicle_timestamp,
            )
        )

    return feed_timestamp, records


def _execute_ddl(connection: psycopg.Connection[Any]) -> None:
    connection.execute(DDL_FILE.read_text(encoding="utf-8"))


def load_live_vehicle_positions(
    *,
    api_key: str | None = None,
    agency_id: str = DEFAULT_AGENCY_ID,
    source_system: str = DEFAULT_SOURCE_SYSTEM,
    feed_scope: str = DEFAULT_FEED_SCOPE,
    timeout_seconds: int = 30,
    payload: bytes | None = None,
    connection_url: str | None = None,
) -> LiveVehicleIngestResult:
    fetched_at = datetime.now(tz=UTC)
    if payload is None:
        effective_api_key = api_key or get_511_api_key()
        vehicle_payload = fetch_vehicle_positions_bytes(
            api_key=effective_api_key,
            agency_id=agency_id,
            timeout_seconds=timeout_seconds,
        )
    else:
        vehicle_payload = payload
    feed_timestamp, records = parse_vehicle_positions_feed(
        vehicle_payload,
        agency_id=agency_id,
        source_system=source_system,
        feed_scope=feed_scope,
        fetched_at=fetched_at,
    )

    effective_connection_url = connection_url or build_postgres_connection_url()
    if connection_url is None:
        settings = get_postgres_settings()
        ensure_db_service()
        wait_for_database(settings)
    with psycopg.connect(effective_connection_url) as connection:
        _execute_ddl(connection)
        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE realtime.vehicle_positions_current;")
            if records:
                cursor.executemany(
                    """
                    INSERT INTO realtime.vehicle_positions_current (
                        agency_id,
                        entity_id,
                        vehicle_id,
                        vehicle_label,
                        route_id,
                        route_short_name,
                        trip_id,
                        stop_id,
                        current_stop_sequence,
                        current_status,
                        occupancy_status,
                        latitude,
                        longitude,
                        bearing,
                        speed_meters_per_second,
                        vehicle_timestamp,
                        feed_timestamp,
                        source_system,
                        feed_scope,
                        fetched_at,
                        ingested_at,
                        geom
                    )
                    VALUES (
                        %(agency_id)s,
                        %(entity_id)s,
                        %(vehicle_id)s,
                        %(vehicle_label)s,
                        %(route_id)s,
                        %(route_short_name)s,
                        %(trip_id)s,
                        %(stop_id)s,
                        %(current_stop_sequence)s,
                        %(current_status)s,
                        %(occupancy_status)s,
                        %(latitude)s,
                        %(longitude)s,
                        %(bearing)s,
                        %(speed_meters_per_second)s,
                        %(vehicle_timestamp)s,
                        %(feed_timestamp)s,
                        %(source_system)s,
                        %(feed_scope)s,
                        %(fetched_at)s,
                        %(fetched_at)s,
                        ST_SetSRID(ST_MakePoint(%(longitude)s, %(latitude)s), 4326)
                    );
                    """,
                    [asdict(record) for record in records],
                )
        connection.commit()

    live_route_ids = sorted(
        {
            record.route_id
            for record in records
            if record.route_id
        }
    )
    live_route_short_names = sorted(
        {
            record.route_short_name
            for record in records
            if record.route_short_name
        }
    )
    return LiveVehicleIngestResult(
        agency_id=agency_id,
        fetched_at=fetched_at.isoformat(),
        feed_timestamp=feed_timestamp.isoformat() if feed_timestamp else None,
        inserted_row_count=len(records),
        route_ids_with_live_vehicles=live_route_ids,
        route_short_names_with_live_vehicles=live_route_short_names,
        source_system=source_system,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--agency-id",
        default=DEFAULT_AGENCY_ID,
        help="Transit agency code for 511 GTFS-RT vehicle positions.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=30,
        help="HTTP timeout for the GTFS-RT request.",
    )
    args = parser.parse_args()

    result = load_live_vehicle_positions(
        agency_id=args.agency_id,
        timeout_seconds=args.timeout_seconds,
    )
    print(json.dumps(asdict(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
