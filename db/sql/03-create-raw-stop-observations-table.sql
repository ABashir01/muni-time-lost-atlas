CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.stop_observations (
    service_date DATE NOT NULL,
    trip_id TEXT NOT NULL,
    stop_id TEXT NOT NULL,
    stop_sequence INTEGER NOT NULL,
    observed_arrival_time TEXT NOT NULL,
    observed_arrival_ts TIMESTAMPTZ NOT NULL,
    source_system TEXT NOT NULL,
    feed_scope TEXT NOT NULL,
    operator_id TEXT,
    snapshot_label TEXT NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL
);
