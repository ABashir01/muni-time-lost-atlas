CREATE SCHEMA IF NOT EXISTS realtime;

CREATE TABLE IF NOT EXISTS realtime.vehicle_positions_current (
    agency_id TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    vehicle_id TEXT,
    vehicle_label TEXT,
    route_id TEXT,
    route_short_name TEXT,
    trip_id TEXT,
    stop_id TEXT,
    current_stop_sequence INTEGER,
    current_status TEXT,
    occupancy_status TEXT,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    bearing DOUBLE PRECISION,
    speed_meters_per_second DOUBLE PRECISION,
    vehicle_timestamp TIMESTAMPTZ,
    feed_timestamp TIMESTAMPTZ,
    source_system TEXT NOT NULL,
    feed_scope TEXT NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL,
    geom geometry(Point, 4326) NOT NULL,
    PRIMARY KEY (agency_id, entity_id)
);

CREATE INDEX IF NOT EXISTS idx_vehicle_positions_current_route_id
    ON realtime.vehicle_positions_current (route_id);

CREATE INDEX IF NOT EXISTS idx_vehicle_positions_current_vehicle_timestamp
    ON realtime.vehicle_positions_current (vehicle_timestamp DESC);

