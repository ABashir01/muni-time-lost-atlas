CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.transit_only_lanes (
    overlay_id TEXT NOT NULL,
    street_name TEXT NOT NULL,
    segment_name TEXT NOT NULL,
    route_hint TEXT,
    geom_geojson TEXT NOT NULL,
    source_system TEXT NOT NULL,
    feed_scope TEXT NOT NULL,
    operator_id TEXT,
    snapshot_label TEXT NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL
);
