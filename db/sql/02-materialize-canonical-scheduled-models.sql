CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS canonical;

DROP VIEW IF EXISTS canonical.observed_stop_events;
DROP VIEW IF EXISTS canonical.observed_stop_event_join_summary;
DROP VIEW IF EXISTS canonical.observed_stop_event_join_audit;

DROP TABLE IF EXISTS canonical.scheduled_stop_events;
DROP TABLE IF EXISTS canonical.service_dates;
DROP TABLE IF EXISTS canonical.scheduled_trips;
DROP TABLE IF EXISTS canonical.scheduled_stops;
DROP TABLE IF EXISTS canonical.scheduled_routes;

DROP TABLE IF EXISTS staging.gtfs_service_dates;
DROP TABLE IF EXISTS staging.gtfs_shapes;
DROP TABLE IF EXISTS staging.gtfs_stop_times;
DROP TABLE IF EXISTS staging.gtfs_stops;
DROP TABLE IF EXISTS staging.gtfs_trips;
DROP TABLE IF EXISTS staging.gtfs_routes;

CREATE TABLE staging.gtfs_routes (
    route_id TEXT NOT NULL,
    agency_id TEXT,
    route_short_name TEXT,
    route_long_name TEXT,
    route_type INTEGER,
    route_color TEXT,
    route_text_color TEXT,
    source_system TEXT NOT NULL,
    feed_scope TEXT NOT NULL,
    operator_id TEXT,
    snapshot_label TEXT NOT NULL
);

INSERT INTO staging.gtfs_routes (
    route_id,
    agency_id,
    route_short_name,
    route_long_name,
    route_type,
    route_color,
    route_text_color,
    source_system,
    feed_scope,
    operator_id,
    snapshot_label
)
SELECT DISTINCT
    route_id,
    NULLIF(agency_id, ''),
    NULLIF(route_short_name, ''),
    NULLIF(route_long_name, ''),
    NULLIF(route_type, '')::INTEGER,
    NULLIF(route_color, ''),
    NULLIF(route_text_color, ''),
    source_system,
    feed_scope,
    NULLIF(operator_id, ''),
    snapshot_label
FROM raw.gtfs_routes
WHERE feed_scope = 'operator_active'
  AND snapshot_label = (
      SELECT snapshot_label
      FROM raw.gtfs_routes
      WHERE feed_scope = 'operator_active'
      ORDER BY ingested_at DESC
      LIMIT 1
  );

CREATE TABLE staging.gtfs_trips (
    route_id TEXT NOT NULL,
    service_id TEXT NOT NULL,
    trip_id TEXT NOT NULL,
    trip_headsign TEXT,
    direction_id INTEGER,
    shape_id TEXT,
    source_system TEXT NOT NULL,
    feed_scope TEXT NOT NULL,
    operator_id TEXT,
    snapshot_label TEXT NOT NULL
);

INSERT INTO staging.gtfs_trips (
    route_id,
    service_id,
    trip_id,
    trip_headsign,
    direction_id,
    shape_id,
    source_system,
    feed_scope,
    operator_id,
    snapshot_label
)
SELECT DISTINCT
    route_id,
    service_id,
    trip_id,
    NULLIF(trip_headsign, ''),
    NULLIF(direction_id, '')::INTEGER,
    NULLIF(shape_id, ''),
    source_system,
    feed_scope,
    NULLIF(operator_id, ''),
    snapshot_label
FROM raw.gtfs_trips
WHERE feed_scope = 'operator_active'
  AND snapshot_label = (
      SELECT snapshot_label
      FROM raw.gtfs_routes
      WHERE feed_scope = 'operator_active'
      ORDER BY ingested_at DESC
      LIMIT 1
  );

CREATE TABLE staging.gtfs_stops (
    stop_id TEXT NOT NULL,
    stop_name TEXT,
    stop_lat DOUBLE PRECISION,
    stop_lon DOUBLE PRECISION,
    source_system TEXT NOT NULL,
    feed_scope TEXT NOT NULL,
    operator_id TEXT,
    snapshot_label TEXT NOT NULL
);

INSERT INTO staging.gtfs_stops (
    stop_id,
    stop_name,
    stop_lat,
    stop_lon,
    source_system,
    feed_scope,
    operator_id,
    snapshot_label
)
SELECT DISTINCT
    stop_id,
    NULLIF(stop_name, ''),
    NULLIF(stop_lat, '')::DOUBLE PRECISION,
    NULLIF(stop_lon, '')::DOUBLE PRECISION,
    source_system,
    feed_scope,
    NULLIF(operator_id, ''),
    snapshot_label
FROM raw.gtfs_stops
WHERE feed_scope = 'operator_active'
  AND snapshot_label = (
      SELECT snapshot_label
      FROM raw.gtfs_routes
      WHERE feed_scope = 'operator_active'
      ORDER BY ingested_at DESC
      LIMIT 1
  );

CREATE TABLE staging.gtfs_stop_times (
    trip_id TEXT NOT NULL,
    arrival_time_text TEXT,
    departure_time_text TEXT,
    stop_id TEXT NOT NULL,
    stop_sequence INTEGER NOT NULL,
    shape_dist_traveled DOUBLE PRECISION,
    arrival_time_secs INTEGER,
    departure_time_secs INTEGER,
    source_system TEXT NOT NULL,
    feed_scope TEXT NOT NULL,
    operator_id TEXT,
    snapshot_label TEXT NOT NULL
);

INSERT INTO staging.gtfs_stop_times (
    trip_id,
    arrival_time_text,
    departure_time_text,
    stop_id,
    stop_sequence,
    shape_dist_traveled,
    arrival_time_secs,
    departure_time_secs,
    source_system,
    feed_scope,
    operator_id,
    snapshot_label
)
SELECT
    trip_id,
    NULLIF(arrival_time, ''),
    NULLIF(departure_time, ''),
    stop_id,
    NULLIF(stop_sequence, '')::INTEGER,
    NULLIF(shape_dist_traveled, '')::DOUBLE PRECISION,
    CASE
        WHEN NULLIF(arrival_time, '') IS NULL THEN NULL
        ELSE (
            split_part(arrival_time, ':', 1)::INTEGER * 3600
            + split_part(arrival_time, ':', 2)::INTEGER * 60
            + split_part(arrival_time, ':', 3)::INTEGER
        )
    END,
    CASE
        WHEN NULLIF(departure_time, '') IS NULL THEN NULL
        ELSE (
            split_part(departure_time, ':', 1)::INTEGER * 3600
            + split_part(departure_time, ':', 2)::INTEGER * 60
            + split_part(departure_time, ':', 3)::INTEGER
        )
    END,
    source_system,
    feed_scope,
    NULLIF(operator_id, ''),
    snapshot_label
FROM raw.gtfs_stop_times
WHERE feed_scope = 'operator_active'
  AND snapshot_label = (
      SELECT snapshot_label
      FROM raw.gtfs_routes
      WHERE feed_scope = 'operator_active'
      ORDER BY ingested_at DESC
      LIMIT 1
  );

CREATE TABLE staging.gtfs_shapes (
    shape_id TEXT NOT NULL,
    shape_pt_lat DOUBLE PRECISION,
    shape_pt_lon DOUBLE PRECISION,
    shape_pt_sequence INTEGER NOT NULL,
    shape_dist_traveled DOUBLE PRECISION,
    source_system TEXT NOT NULL,
    feed_scope TEXT NOT NULL,
    operator_id TEXT,
    snapshot_label TEXT NOT NULL
);

INSERT INTO staging.gtfs_shapes (
    shape_id,
    shape_pt_lat,
    shape_pt_lon,
    shape_pt_sequence,
    shape_dist_traveled,
    source_system,
    feed_scope,
    operator_id,
    snapshot_label
)
SELECT
    shape_id,
    NULLIF(shape_pt_lat, '')::DOUBLE PRECISION,
    NULLIF(shape_pt_lon, '')::DOUBLE PRECISION,
    NULLIF(shape_pt_sequence, '')::INTEGER,
    NULLIF(shape_dist_traveled, '')::DOUBLE PRECISION,
    source_system,
    feed_scope,
    NULLIF(operator_id, ''),
    snapshot_label
FROM raw.gtfs_shapes
WHERE feed_scope = 'operator_active'
  AND snapshot_label = (
      SELECT snapshot_label
      FROM raw.gtfs_routes
      WHERE feed_scope = 'operator_active'
      ORDER BY ingested_at DESC
      LIMIT 1
  );

CREATE TABLE staging.gtfs_service_dates (
    service_id TEXT NOT NULL,
    service_date DATE NOT NULL,
    source_system TEXT NOT NULL,
    feed_scope TEXT NOT NULL,
    operator_id TEXT,
    snapshot_label TEXT NOT NULL
);

WITH latest_snapshot AS (
    SELECT snapshot_label
    FROM raw.gtfs_routes
    WHERE feed_scope = 'operator_active'
    ORDER BY ingested_at DESC
    LIMIT 1
),
calendar_expanded AS (
    SELECT
        calendar.service_id,
        service_day::DATE AS service_date,
        calendar.source_system,
        calendar.feed_scope,
        NULLIF(calendar.operator_id, '') AS operator_id,
        calendar.snapshot_label
    FROM raw.gtfs_calendar AS calendar
    CROSS JOIN latest_snapshot
    CROSS JOIN LATERAL generate_series(
        TO_DATE(calendar.start_date, 'YYYYMMDD'),
        TO_DATE(calendar.end_date, 'YYYYMMDD'),
        INTERVAL '1 day'
    ) AS service_day
    WHERE calendar.feed_scope = 'operator_active'
      AND calendar.snapshot_label = latest_snapshot.snapshot_label
      AND CASE EXTRACT(ISODOW FROM service_day)::INTEGER
          WHEN 1 THEN calendar.monday = '1'
          WHEN 2 THEN calendar.tuesday = '1'
          WHEN 3 THEN calendar.wednesday = '1'
          WHEN 4 THEN calendar.thursday = '1'
          WHEN 5 THEN calendar.friday = '1'
          WHEN 6 THEN calendar.saturday = '1'
          WHEN 7 THEN calendar.sunday = '1'
          ELSE FALSE
      END
),
calendar_date_additions AS (
    SELECT
        calendar_dates.service_id,
        TO_DATE(calendar_dates.date, 'YYYYMMDD') AS service_date,
        calendar_dates.source_system,
        calendar_dates.feed_scope,
        NULLIF(calendar_dates.operator_id, '') AS operator_id,
        calendar_dates.snapshot_label
    FROM raw.gtfs_calendar_dates AS calendar_dates
    CROSS JOIN latest_snapshot
    WHERE calendar_dates.feed_scope = 'operator_active'
      AND calendar_dates.snapshot_label = latest_snapshot.snapshot_label
      AND calendar_dates.exception_type = '1'
),
calendar_date_removals AS (
    SELECT
        calendar_dates.service_id,
        TO_DATE(calendar_dates.date, 'YYYYMMDD') AS service_date
    FROM raw.gtfs_calendar_dates AS calendar_dates
    CROSS JOIN latest_snapshot
    WHERE calendar_dates.feed_scope = 'operator_active'
      AND calendar_dates.snapshot_label = latest_snapshot.snapshot_label
      AND calendar_dates.exception_type = '2'
),
combined_service_dates AS (
    SELECT * FROM calendar_expanded
    UNION
    SELECT * FROM calendar_date_additions
)
INSERT INTO staging.gtfs_service_dates (
    service_id,
    service_date,
    source_system,
    feed_scope,
    operator_id,
    snapshot_label
)
SELECT DISTINCT
    combined.service_id,
    combined.service_date,
    combined.source_system,
    combined.feed_scope,
    combined.operator_id,
    combined.snapshot_label
FROM combined_service_dates AS combined
LEFT JOIN calendar_date_removals AS removals
  ON combined.service_id = removals.service_id
 AND combined.service_date = removals.service_date
WHERE removals.service_id IS NULL;

CREATE TABLE canonical.scheduled_routes (
    route_id TEXT PRIMARY KEY,
    agency_id TEXT,
    route_short_name TEXT,
    route_long_name TEXT,
    route_type INTEGER,
    route_color TEXT,
    route_text_color TEXT,
    source_system TEXT NOT NULL,
    feed_scope TEXT NOT NULL,
    operator_id TEXT,
    snapshot_label TEXT NOT NULL
);

INSERT INTO canonical.scheduled_routes (
    route_id,
    agency_id,
    route_short_name,
    route_long_name,
    route_type,
    route_color,
    route_text_color,
    source_system,
    feed_scope,
    operator_id,
    snapshot_label
)
SELECT
    route_id,
    agency_id,
    route_short_name,
    route_long_name,
    route_type,
    route_color,
    route_text_color,
    source_system,
    feed_scope,
    operator_id,
    snapshot_label
FROM staging.gtfs_routes;

CREATE TABLE canonical.scheduled_stops (
    stop_id TEXT PRIMARY KEY,
    stop_name TEXT,
    stop_lat DOUBLE PRECISION,
    stop_lon DOUBLE PRECISION,
    source_system TEXT NOT NULL,
    feed_scope TEXT NOT NULL,
    operator_id TEXT,
    snapshot_label TEXT NOT NULL
);

INSERT INTO canonical.scheduled_stops (
    stop_id,
    stop_name,
    stop_lat,
    stop_lon,
    source_system,
    feed_scope,
    operator_id,
    snapshot_label
)
SELECT
    stop_id,
    stop_name,
    stop_lat,
    stop_lon,
    source_system,
    feed_scope,
    operator_id,
    snapshot_label
FROM staging.gtfs_stops;

CREATE TABLE canonical.scheduled_trips (
    trip_id TEXT PRIMARY KEY,
    route_id TEXT NOT NULL REFERENCES canonical.scheduled_routes(route_id),
    service_id TEXT NOT NULL,
    trip_headsign TEXT,
    direction_id INTEGER,
    shape_id TEXT,
    source_system TEXT NOT NULL,
    feed_scope TEXT NOT NULL,
    operator_id TEXT,
    snapshot_label TEXT NOT NULL
);

INSERT INTO canonical.scheduled_trips (
    trip_id,
    route_id,
    service_id,
    trip_headsign,
    direction_id,
    shape_id,
    source_system,
    feed_scope,
    operator_id,
    snapshot_label
)
SELECT
    trip_id,
    route_id,
    service_id,
    trip_headsign,
    direction_id,
    shape_id,
    source_system,
    feed_scope,
    operator_id,
    snapshot_label
FROM staging.gtfs_trips;

CREATE TABLE canonical.service_dates (
    service_id TEXT NOT NULL,
    service_date DATE NOT NULL,
    source_system TEXT NOT NULL,
    feed_scope TEXT NOT NULL,
    operator_id TEXT,
    snapshot_label TEXT NOT NULL,
    PRIMARY KEY (service_id, service_date)
);

INSERT INTO canonical.service_dates (
    service_id,
    service_date,
    source_system,
    feed_scope,
    operator_id,
    snapshot_label
)
SELECT
    service_id,
    service_date,
    source_system,
    feed_scope,
    operator_id,
    snapshot_label
FROM staging.gtfs_service_dates;

CREATE TABLE canonical.scheduled_stop_events (
    trip_id TEXT NOT NULL REFERENCES canonical.scheduled_trips(trip_id),
    route_id TEXT NOT NULL REFERENCES canonical.scheduled_routes(route_id),
    service_id TEXT NOT NULL,
    service_date DATE NOT NULL,
    stop_id TEXT NOT NULL REFERENCES canonical.scheduled_stops(stop_id),
    stop_sequence INTEGER NOT NULL,
    trip_headsign TEXT,
    direction_id INTEGER,
    shape_id TEXT,
    arrival_time_text TEXT,
    departure_time_text TEXT,
    arrival_time_secs INTEGER,
    departure_time_secs INTEGER,
    shape_dist_traveled DOUBLE PRECISION,
    source_system TEXT NOT NULL,
    feed_scope TEXT NOT NULL,
    operator_id TEXT,
    snapshot_label TEXT NOT NULL,
    PRIMARY KEY (trip_id, service_date, stop_sequence),
    FOREIGN KEY (service_id, service_date)
        REFERENCES canonical.service_dates(service_id, service_date)
);

INSERT INTO canonical.scheduled_stop_events (
    trip_id,
    route_id,
    service_id,
    service_date,
    stop_id,
    stop_sequence,
    trip_headsign,
    direction_id,
    shape_id,
    arrival_time_text,
    departure_time_text,
    arrival_time_secs,
    departure_time_secs,
    shape_dist_traveled,
    source_system,
    feed_scope,
    operator_id,
    snapshot_label
)
SELECT
    trips.trip_id,
    trips.route_id,
    trips.service_id,
    service_dates.service_date,
    stop_times.stop_id,
    stop_times.stop_sequence,
    trips.trip_headsign,
    trips.direction_id,
    trips.shape_id,
    stop_times.arrival_time_text,
    stop_times.departure_time_text,
    stop_times.arrival_time_secs,
    stop_times.departure_time_secs,
    stop_times.shape_dist_traveled,
    trips.source_system,
    trips.feed_scope,
    trips.operator_id,
    trips.snapshot_label
FROM canonical.scheduled_trips AS trips
JOIN canonical.service_dates AS service_dates
  ON trips.service_id = service_dates.service_id
JOIN staging.gtfs_stop_times AS stop_times
  ON trips.trip_id = stop_times.trip_id;
