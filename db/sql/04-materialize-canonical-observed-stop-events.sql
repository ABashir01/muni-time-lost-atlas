CREATE SCHEMA IF NOT EXISTS canonical;

DROP VIEW IF EXISTS canonical.observed_stop_events;
DROP VIEW IF EXISTS canonical.observed_stop_event_join_summary;
DROP VIEW IF EXISTS canonical.observed_stop_event_join_audit;

CREATE VIEW canonical.observed_stop_event_join_audit AS
WITH observed_base AS (
    SELECT
        observations.service_date,
        observations.trip_id,
        observations.stop_id,
        observations.stop_sequence,
        observations.observed_arrival_time,
        observations.observed_arrival_ts,
        observations.source_system AS observed_source_system,
        observations.feed_scope AS observed_feed_scope,
        observations.operator_id AS observed_operator_id,
        observations.snapshot_label AS observed_snapshot_label,
        observations.ingested_at AS observed_ingested_at,
        COUNT(*) OVER (
            PARTITION BY
                observations.service_date,
                observations.trip_id,
                observations.stop_id,
                observations.stop_sequence,
                observations.snapshot_label
        ) AS observation_key_row_count
    FROM raw.stop_observations AS observations
),
trip_service_candidates AS (
    SELECT
        observed.service_date,
        observed.trip_id,
        COUNT(scheduled.trip_id) AS scheduled_trip_service_date_count
    FROM observed_base AS observed
    LEFT JOIN canonical.scheduled_stop_events AS scheduled
      ON scheduled.service_date = observed.service_date
     AND scheduled.trip_id = observed.trip_id
    GROUP BY
        observed.service_date,
        observed.trip_id
),
trip_service_sequence_candidates AS (
    SELECT
        observed.service_date,
        observed.trip_id,
        observed.stop_sequence,
        COUNT(scheduled.trip_id) AS scheduled_trip_service_sequence_count
    FROM observed_base AS observed
    LEFT JOIN canonical.scheduled_stop_events AS scheduled
      ON scheduled.service_date = observed.service_date
     AND scheduled.trip_id = observed.trip_id
     AND scheduled.stop_sequence = observed.stop_sequence
    GROUP BY
        observed.service_date,
        observed.trip_id,
        observed.stop_sequence
)
SELECT
    observed.service_date,
    observed.trip_id,
    scheduled.route_id,
    scheduled.service_id,
    observed.stop_id AS observed_stop_id,
    scheduled.stop_id AS scheduled_stop_id,
    observed.stop_sequence,
    scheduled.trip_headsign,
    scheduled.direction_id,
    scheduled.shape_id,
    scheduled.shape_dist_traveled,
    scheduled.arrival_time_text AS scheduled_arrival_time_text,
    scheduled.departure_time_text AS scheduled_departure_time_text,
    scheduled.arrival_time_secs AS scheduled_arrival_time_secs,
    scheduled.departure_time_secs AS scheduled_departure_time_secs,
    CASE
        WHEN scheduled.arrival_time_secs IS NULL THEN NULL
        ELSE (
            observed.service_date::TIMESTAMP
            + scheduled.arrival_time_secs * INTERVAL '1 second'
        ) AT TIME ZONE 'America/Los_Angeles'
    END AS scheduled_arrival_ts,
    CASE
        WHEN scheduled.departure_time_secs IS NULL THEN NULL
        ELSE (
            observed.service_date::TIMESTAMP
            + scheduled.departure_time_secs * INTERVAL '1 second'
        ) AT TIME ZONE 'America/Los_Angeles'
    END AS scheduled_departure_ts,
    observed.observed_arrival_time,
    observed.observed_arrival_ts,
    CASE
        WHEN scheduled.arrival_time_secs IS NULL THEN NULL
        ELSE EXTRACT(
            EPOCH FROM (
                observed.observed_arrival_ts
                - (
                    observed.service_date::TIMESTAMP
                    + scheduled.arrival_time_secs * INTERVAL '1 second'
                ) AT TIME ZONE 'America/Los_Angeles'
            )
        )::INTEGER
    END AS arrival_delay_secs,
    observed.observed_source_system,
    observed.observed_feed_scope,
    observed.observed_operator_id,
    observed.observed_snapshot_label,
    observed.observed_ingested_at,
    scheduled.source_system AS scheduled_source_system,
    scheduled.feed_scope AS scheduled_feed_scope,
    scheduled.operator_id AS scheduled_operator_id,
    scheduled.snapshot_label AS scheduled_snapshot_label,
    observed.observation_key_row_count,
    trip_candidates.scheduled_trip_service_date_count,
    sequence_candidates.scheduled_trip_service_sequence_count,
    CASE
        WHEN observed.observation_key_row_count > 1 THEN 'duplicate_observation_key'
        WHEN scheduled.trip_id IS NOT NULL THEN 'matched_exact'
        WHEN COALESCE(trip_candidates.scheduled_trip_service_date_count, 0) = 0 THEN 'unmatched_trip_service_date'
        WHEN COALESCE(sequence_candidates.scheduled_trip_service_sequence_count, 0) = 0 THEN 'unmatched_stop_sequence'
        ELSE 'unmatched_stop_id'
    END AS join_status
FROM observed_base AS observed
LEFT JOIN canonical.scheduled_stop_events AS scheduled
  ON scheduled.service_date = observed.service_date
 AND scheduled.trip_id = observed.trip_id
 AND scheduled.stop_sequence = observed.stop_sequence
 AND scheduled.stop_id = observed.stop_id
LEFT JOIN trip_service_candidates AS trip_candidates
  ON trip_candidates.service_date = observed.service_date
 AND trip_candidates.trip_id = observed.trip_id
LEFT JOIN trip_service_sequence_candidates AS sequence_candidates
  ON sequence_candidates.service_date = observed.service_date
 AND sequence_candidates.trip_id = observed.trip_id
 AND sequence_candidates.stop_sequence = observed.stop_sequence;

CREATE VIEW canonical.observed_stop_event_join_summary AS
SELECT
    observed_snapshot_label,
    join_status,
    COUNT(*) AS row_count
FROM canonical.observed_stop_event_join_audit
GROUP BY observed_snapshot_label, join_status
ORDER BY observed_snapshot_label, join_status;

CREATE VIEW canonical.observed_stop_events AS
SELECT
    service_date,
    trip_id,
    route_id,
    service_id,
    observed_stop_id AS stop_id,
    scheduled_stop_id,
    stop_sequence,
    trip_headsign,
    direction_id,
    shape_id,
    shape_dist_traveled,
    scheduled_arrival_time_text,
    scheduled_departure_time_text,
    scheduled_arrival_time_secs,
    scheduled_departure_time_secs,
    scheduled_arrival_ts,
    scheduled_departure_ts,
    observed_arrival_time,
    observed_arrival_ts,
    arrival_delay_secs,
    observed_source_system,
    observed_feed_scope,
    observed_operator_id,
    observed_snapshot_label,
    observed_ingested_at,
    scheduled_source_system,
    scheduled_feed_scope,
    scheduled_operator_id,
    scheduled_snapshot_label
FROM canonical.observed_stop_event_join_audit
WHERE join_status = 'matched_exact';
