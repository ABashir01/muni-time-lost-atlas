CREATE SCHEMA IF NOT EXISTS raw;

DROP TABLE IF EXISTS raw.gtfs_stop_times;
DROP TABLE IF EXISTS raw.gtfs_shapes;
DROP TABLE IF EXISTS raw.gtfs_trips;
DROP TABLE IF EXISTS raw.gtfs_stops;
DROP TABLE IF EXISTS raw.gtfs_routes;
DROP TABLE IF EXISTS raw.gtfs_calendar_dates;
DROP TABLE IF EXISTS raw.gtfs_calendar;

CREATE TABLE IF NOT EXISTS raw.gtfs_routes (
    route_id TEXT,
    agency_id TEXT,
    route_short_name TEXT,
    route_long_name TEXT,
    route_type TEXT,
    route_color TEXT,
    route_text_color TEXT,
    source_system TEXT NOT NULL,
    feed_scope TEXT NOT NULL,
    operator_id TEXT,
    snapshot_label TEXT NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.gtfs_trips (
    route_id TEXT,
    service_id TEXT,
    trip_id TEXT,
    trip_headsign TEXT,
    direction_id TEXT,
    shape_id TEXT,
    source_system TEXT NOT NULL,
    feed_scope TEXT NOT NULL,
    operator_id TEXT,
    snapshot_label TEXT NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.gtfs_stops (
    stop_id TEXT,
    stop_name TEXT,
    stop_lat TEXT,
    stop_lon TEXT,
    source_system TEXT NOT NULL,
    feed_scope TEXT NOT NULL,
    operator_id TEXT,
    snapshot_label TEXT NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.gtfs_stop_times (
    trip_id TEXT,
    arrival_time TEXT,
    departure_time TEXT,
    stop_id TEXT,
    stop_sequence TEXT,
    shape_dist_traveled TEXT,
    source_system TEXT NOT NULL,
    feed_scope TEXT NOT NULL,
    operator_id TEXT,
    snapshot_label TEXT NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.gtfs_shapes (
    shape_id TEXT,
    shape_pt_lat TEXT,
    shape_pt_lon TEXT,
    shape_pt_sequence TEXT,
    shape_dist_traveled TEXT,
    source_system TEXT NOT NULL,
    feed_scope TEXT NOT NULL,
    operator_id TEXT,
    snapshot_label TEXT NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.gtfs_calendar (
    service_id TEXT,
    monday TEXT,
    tuesday TEXT,
    wednesday TEXT,
    thursday TEXT,
    friday TEXT,
    saturday TEXT,
    sunday TEXT,
    start_date TEXT,
    end_date TEXT,
    source_system TEXT NOT NULL,
    feed_scope TEXT NOT NULL,
    operator_id TEXT,
    snapshot_label TEXT NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.gtfs_calendar_dates (
    service_id TEXT,
    date TEXT,
    exception_type TEXT,
    source_system TEXT NOT NULL,
    feed_scope TEXT NOT NULL,
    operator_id TEXT,
    snapshot_label TEXT NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL
);
