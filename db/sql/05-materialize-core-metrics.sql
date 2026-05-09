CREATE SCHEMA IF NOT EXISTS marts;

DROP TABLE IF EXISTS marts.route_hour_summary;
DROP TABLE IF EXISTS marts.route_direction_summary;
DROP TABLE IF EXISTS marts.route_window_summary;

DROP TABLE IF EXISTS tmp_metric_route_hour_keys;
DROP TABLE IF EXISTS tmp_metric_route_direction_keys;
DROP TABLE IF EXISTS tmp_metric_route_keys;
DROP TABLE IF EXISTS tmp_metric_unmatched_resolved;
DROP TABLE IF EXISTS tmp_metric_matched_stop_event_coverage;
DROP TABLE IF EXISTS tmp_metric_direction_labels;
DROP TABLE IF EXISTS tmp_metric_headway_intervals;
DROP TABLE IF EXISTS tmp_metric_matched_first_stop_events;
DROP TABLE IF EXISTS tmp_metric_full_trip_metrics;
DROP TABLE IF EXISTS tmp_metric_scheduled_trip_terminals;

CREATE TEMP TABLE tmp_metric_scheduled_trip_terminals AS
WITH trip_bounds AS (
    SELECT
        trip_id,
        service_date,
        MIN(stop_sequence) AS first_stop_sequence,
        MAX(stop_sequence) AS last_stop_sequence
    FROM canonical.scheduled_stop_events
    GROUP BY trip_id, service_date
)
SELECT
    first_stop.trip_id,
    first_stop.route_id,
    first_stop.service_id,
    first_stop.service_date,
    first_stop.direction_id,
    first_stop.trip_headsign,
    first_stop.stop_id AS first_stop_id,
    last_stop.stop_id AS last_stop_id,
    first_stop.stop_sequence AS first_stop_sequence,
    last_stop.stop_sequence AS last_stop_sequence,
    first_stop.arrival_time_secs AS first_arrival_time_secs,
    last_stop.arrival_time_secs AS last_arrival_time_secs,
    CASE
        WHEN first_stop.arrival_time_secs IS NULL THEN NULL
        ELSE (
            first_stop.service_date::TIMESTAMP
            + first_stop.arrival_time_secs * INTERVAL '1 second'
        ) AT TIME ZONE 'America/Los_Angeles'
    END AS first_scheduled_arrival_ts,
    CASE
        WHEN last_stop.arrival_time_secs IS NULL THEN NULL
        ELSE (
            last_stop.service_date::TIMESTAMP
            + last_stop.arrival_time_secs * INTERVAL '1 second'
        ) AT TIME ZONE 'America/Los_Angeles'
    END AS last_scheduled_arrival_ts,
    EXTRACT(
        HOUR FROM (
            first_stop.service_date::TIMESTAMP
            + first_stop.arrival_time_secs * INTERVAL '1 second'
        )
    )::INTEGER AS trip_start_hour_local,
    ROW_NUMBER() OVER (
        PARTITION BY
            first_stop.route_id,
            first_stop.direction_id,
            first_stop.stop_id,
            first_stop.service_date
        ORDER BY first_stop.arrival_time_secs, first_stop.trip_id
    ) AS first_stop_trip_order
FROM trip_bounds
JOIN canonical.scheduled_stop_events AS first_stop
  ON first_stop.trip_id = trip_bounds.trip_id
 AND first_stop.service_date = trip_bounds.service_date
 AND first_stop.stop_sequence = trip_bounds.first_stop_sequence
JOIN canonical.scheduled_stop_events AS last_stop
  ON last_stop.trip_id = trip_bounds.trip_id
 AND last_stop.service_date = trip_bounds.service_date
 AND last_stop.stop_sequence = trip_bounds.last_stop_sequence;

CREATE TEMP TABLE tmp_metric_full_trip_metrics AS
SELECT
    terminals.route_id,
    terminals.direction_id,
    terminals.trip_headsign,
    terminals.service_date,
    terminals.trip_id,
    terminals.trip_start_hour_local,
    EXTRACT(
        EPOCH FROM (
            observed_last.observed_arrival_ts
            - observed_first.observed_arrival_ts
        )
    )::NUMERIC AS observed_runtime_secs,
    (terminals.last_arrival_time_secs - terminals.first_arrival_time_secs)::NUMERIC
        AS scheduled_runtime_secs,
    ROUND(
        GREATEST(
            0::NUMERIC,
            (
                EXTRACT(
                    EPOCH FROM (
                        observed_last.observed_arrival_ts
                        - observed_first.observed_arrival_ts
                    )
                )::NUMERIC
                - (terminals.last_arrival_time_secs - terminals.first_arrival_time_secs)::NUMERIC
            ) / 60.0
        ),
        6
    ) AS in_vehicle_loss_minutes
FROM tmp_metric_scheduled_trip_terminals AS terminals
JOIN canonical.observed_stop_events AS observed_first
  ON observed_first.trip_id = terminals.trip_id
 AND observed_first.service_date = terminals.service_date
 AND observed_first.stop_sequence = terminals.first_stop_sequence
 AND observed_first.stop_id = terminals.first_stop_id
JOIN canonical.observed_stop_events AS observed_last
  ON observed_last.trip_id = terminals.trip_id
 AND observed_last.service_date = terminals.service_date
 AND observed_last.stop_sequence = terminals.last_stop_sequence
 AND observed_last.stop_id = terminals.last_stop_id
WHERE terminals.first_scheduled_arrival_ts IS NOT NULL
  AND terminals.last_scheduled_arrival_ts IS NOT NULL
  AND terminals.last_arrival_time_secs IS NOT NULL
  AND terminals.first_arrival_time_secs IS NOT NULL;

CREATE TEMP TABLE tmp_metric_matched_first_stop_events AS
SELECT
    terminals.route_id,
    terminals.direction_id,
    terminals.trip_headsign,
    terminals.service_date,
    terminals.trip_id,
    terminals.first_stop_id,
    terminals.first_stop_trip_order,
    terminals.first_scheduled_arrival_ts,
    observed_first.observed_arrival_ts AS observed_first_arrival_ts
FROM tmp_metric_scheduled_trip_terminals AS terminals
JOIN canonical.observed_stop_events AS observed_first
  ON observed_first.trip_id = terminals.trip_id
 AND observed_first.service_date = terminals.service_date
 AND observed_first.stop_sequence = terminals.first_stop_sequence
 AND observed_first.stop_id = terminals.first_stop_id
WHERE terminals.first_scheduled_arrival_ts IS NOT NULL;

CREATE TEMP TABLE tmp_metric_headway_intervals AS
SELECT
    current_trip.route_id,
    current_trip.direction_id,
    current_trip.trip_headsign,
    current_trip.service_date,
    current_trip.first_stop_id,
    EXTRACT(
        HOUR FROM (
            current_trip.first_scheduled_arrival_ts
            + (
                next_trip.first_scheduled_arrival_ts
                - current_trip.first_scheduled_arrival_ts
            ) / 2
        ) AT TIME ZONE 'America/Los_Angeles'
    )::INTEGER AS hour_local,
    EXTRACT(
        EPOCH FROM (
            next_trip.first_scheduled_arrival_ts
            - current_trip.first_scheduled_arrival_ts
        )
    )::NUMERIC AS scheduled_headway_secs,
    EXTRACT(
        EPOCH FROM (
            next_trip.observed_first_arrival_ts
            - current_trip.observed_first_arrival_ts
        )
    )::NUMERIC AS observed_headway_secs
FROM tmp_metric_matched_first_stop_events AS current_trip
JOIN tmp_metric_matched_first_stop_events AS next_trip
  ON next_trip.route_id = current_trip.route_id
 AND next_trip.direction_id IS NOT DISTINCT FROM current_trip.direction_id
 AND next_trip.first_stop_id = current_trip.first_stop_id
 AND next_trip.service_date = current_trip.service_date
 AND next_trip.first_stop_trip_order = current_trip.first_stop_trip_order + 1
WHERE EXTRACT(
        EPOCH FROM (
            next_trip.first_scheduled_arrival_ts
            - current_trip.first_scheduled_arrival_ts
        )
    ) > 0
  AND EXTRACT(
        EPOCH FROM (
            next_trip.observed_first_arrival_ts
            - current_trip.observed_first_arrival_ts
        )
    ) > 0;

CREATE TEMP TABLE tmp_metric_direction_labels AS
SELECT
    route_id,
    direction_id,
    MIN(trip_headsign) AS direction_label
FROM canonical.scheduled_trips
GROUP BY route_id, direction_id;

CREATE TEMP TABLE tmp_metric_matched_stop_event_coverage AS
SELECT
    route_id,
    direction_id,
    service_date,
    EXTRACT(HOUR FROM scheduled_arrival_ts AT TIME ZONE 'America/Los_Angeles')::INTEGER
        AS hour_local
FROM canonical.observed_stop_events;

CREATE TEMP TABLE tmp_metric_unmatched_resolved AS
SELECT
    COALESCE(audit.route_id, scheduled_trip.route_id) AS route_id,
    COALESCE(audit.direction_id, scheduled_trip.direction_id) AS direction_id,
    audit.service_date,
    EXTRACT(HOUR FROM audit.observed_arrival_ts AT TIME ZONE 'America/Los_Angeles')::INTEGER
        AS hour_local,
    audit.join_status
FROM canonical.observed_stop_event_join_audit AS audit
LEFT JOIN canonical.scheduled_trips AS scheduled_trip
  ON scheduled_trip.trip_id = audit.trip_id
WHERE audit.join_status <> 'matched_exact'
  AND COALESCE(audit.route_id, scheduled_trip.route_id) IS NOT NULL;

CREATE TEMP TABLE tmp_metric_route_keys AS
SELECT route_id FROM tmp_metric_matched_stop_event_coverage
UNION
SELECT route_id FROM tmp_metric_unmatched_resolved
UNION
SELECT route_id FROM tmp_metric_full_trip_metrics
UNION
SELECT route_id FROM tmp_metric_headway_intervals;

CREATE TEMP TABLE tmp_metric_route_direction_keys AS
SELECT route_id, direction_id FROM tmp_metric_matched_stop_event_coverage
UNION
SELECT route_id, direction_id FROM tmp_metric_unmatched_resolved
UNION
SELECT route_id, direction_id FROM tmp_metric_full_trip_metrics
UNION
SELECT route_id, direction_id FROM tmp_metric_headway_intervals;

CREATE TEMP TABLE tmp_metric_route_hour_keys AS
SELECT route_id, direction_id, hour_local FROM tmp_metric_matched_stop_event_coverage
UNION
SELECT route_id, direction_id, hour_local FROM tmp_metric_unmatched_resolved
UNION
SELECT route_id, direction_id, trip_start_hour_local AS hour_local FROM tmp_metric_full_trip_metrics
UNION
SELECT route_id, direction_id, hour_local FROM tmp_metric_headway_intervals;

CREATE TABLE marts.route_window_summary AS
WITH waiting_metrics AS (
    SELECT
        route_id,
        ROUND(
            GREATEST(
                0::NUMERIC,
                (
                    SUM(observed_headway_secs * observed_headway_secs)
                    / (2 * SUM(observed_headway_secs) * 60.0)
                )
                - (
                    SUM(scheduled_headway_secs * scheduled_headway_secs)
                    / (2 * SUM(scheduled_headway_secs) * 60.0)
                )
            ),
            6
        ) AS waiting_loss_minutes,
        COUNT(*) AS matched_headway_interval_count
    FROM tmp_metric_headway_intervals
    GROUP BY route_id
),
runtime_metrics AS (
    SELECT
        route_id,
        ROUND(
            (
                PERCENTILE_CONT(0.5)
                WITHIN GROUP (ORDER BY in_vehicle_loss_minutes)
            )::NUMERIC,
            6
        ) AS in_vehicle_loss_minutes,
        COUNT(*) AS matched_full_trip_count
    FROM tmp_metric_full_trip_metrics
    GROUP BY route_id
),
matched_coverage AS (
    SELECT
        route_id,
        COUNT(*) AS matched_observed_stop_event_count
    FROM tmp_metric_matched_stop_event_coverage
    GROUP BY route_id
),
unmatched_coverage AS (
    SELECT
        route_id,
        COUNT(*) AS resolved_unmatched_observation_count
    FROM tmp_metric_unmatched_resolved
    GROUP BY route_id
)
SELECT
    route_keys.route_id,
    COALESCE(routes.route_long_name, routes.route_short_name, route_keys.route_id) AS route_name,
    routes.route_short_name,
    routes.route_long_name,
    'all_day'::TEXT AS window_key,
    CASE
        WHEN waiting_metrics.waiting_loss_minutes IS NOT NULL
         AND runtime_metrics.in_vehicle_loss_minutes IS NOT NULL
        THEN ROUND(
            waiting_metrics.waiting_loss_minutes
            + runtime_metrics.in_vehicle_loss_minutes,
            6
        )
        ELSE NULL
    END AS typical_trip_loss_minutes,
    waiting_metrics.waiting_loss_minutes,
    runtime_metrics.in_vehicle_loss_minutes,
    COALESCE(matched_coverage.matched_observed_stop_event_count, 0)
        AS matched_observed_stop_event_count,
    COALESCE(unmatched_coverage.resolved_unmatched_observation_count, 0)
        AS resolved_unmatched_observation_count,
    COALESCE(waiting_metrics.matched_headway_interval_count, 0)
        AS matched_headway_interval_count,
    COALESCE(runtime_metrics.matched_full_trip_count, 0)
        AS matched_full_trip_count,
    CURRENT_TIMESTAMP AS metric_updated_at
FROM tmp_metric_route_keys AS route_keys
JOIN canonical.scheduled_routes AS routes
  ON routes.route_id = route_keys.route_id
LEFT JOIN waiting_metrics
  ON waiting_metrics.route_id = route_keys.route_id
LEFT JOIN runtime_metrics
  ON runtime_metrics.route_id = route_keys.route_id
LEFT JOIN matched_coverage
  ON matched_coverage.route_id = route_keys.route_id
LEFT JOIN unmatched_coverage
  ON unmatched_coverage.route_id = route_keys.route_id;

CREATE INDEX route_window_summary_route_idx
    ON marts.route_window_summary (route_id, window_key);

CREATE INDEX route_window_summary_loss_idx
    ON marts.route_window_summary (window_key, typical_trip_loss_minutes DESC NULLS LAST);

CREATE TABLE marts.route_direction_summary AS
WITH waiting_metrics AS (
    SELECT
        route_id,
        direction_id,
        ROUND(
            GREATEST(
                0::NUMERIC,
                (
                    SUM(observed_headway_secs * observed_headway_secs)
                    / (2 * SUM(observed_headway_secs) * 60.0)
                )
                - (
                    SUM(scheduled_headway_secs * scheduled_headway_secs)
                    / (2 * SUM(scheduled_headway_secs) * 60.0)
                )
            ),
            6
        ) AS waiting_loss_minutes,
        COUNT(*) AS matched_headway_interval_count
    FROM tmp_metric_headway_intervals
    GROUP BY route_id, direction_id
),
runtime_metrics AS (
    SELECT
        route_id,
        direction_id,
        ROUND(
            (
                PERCENTILE_CONT(0.5)
                WITHIN GROUP (ORDER BY in_vehicle_loss_minutes)
            )::NUMERIC,
            6
        ) AS in_vehicle_loss_minutes,
        COUNT(*) AS matched_full_trip_count
    FROM tmp_metric_full_trip_metrics
    GROUP BY route_id, direction_id
),
matched_coverage AS (
    SELECT
        route_id,
        direction_id,
        COUNT(*) AS matched_observed_stop_event_count
    FROM tmp_metric_matched_stop_event_coverage
    GROUP BY route_id, direction_id
),
unmatched_coverage AS (
    SELECT
        route_id,
        direction_id,
        COUNT(*) AS resolved_unmatched_observation_count
    FROM tmp_metric_unmatched_resolved
    GROUP BY route_id, direction_id
)
SELECT
    direction_keys.route_id,
    COALESCE(routes.route_long_name, routes.route_short_name, direction_keys.route_id) AS route_name,
    routes.route_short_name,
    routes.route_long_name,
    direction_keys.direction_id,
    direction_labels.direction_label,
    'all_day'::TEXT AS window_key,
    CASE
        WHEN waiting_metrics.waiting_loss_minutes IS NOT NULL
         AND runtime_metrics.in_vehicle_loss_minutes IS NOT NULL
        THEN ROUND(
            waiting_metrics.waiting_loss_minutes
            + runtime_metrics.in_vehicle_loss_minutes,
            6
        )
        ELSE NULL
    END AS typical_trip_loss_minutes,
    waiting_metrics.waiting_loss_minutes,
    runtime_metrics.in_vehicle_loss_minutes,
    COALESCE(matched_coverage.matched_observed_stop_event_count, 0)
        AS matched_observed_stop_event_count,
    COALESCE(unmatched_coverage.resolved_unmatched_observation_count, 0)
        AS resolved_unmatched_observation_count,
    COALESCE(waiting_metrics.matched_headway_interval_count, 0)
        AS matched_headway_interval_count,
    COALESCE(runtime_metrics.matched_full_trip_count, 0)
        AS matched_full_trip_count,
    CURRENT_TIMESTAMP AS metric_updated_at
FROM tmp_metric_route_direction_keys AS direction_keys
JOIN canonical.scheduled_routes AS routes
  ON routes.route_id = direction_keys.route_id
LEFT JOIN tmp_metric_direction_labels AS direction_labels
  ON direction_labels.route_id = direction_keys.route_id
 AND direction_labels.direction_id IS NOT DISTINCT FROM direction_keys.direction_id
LEFT JOIN waiting_metrics
  ON waiting_metrics.route_id = direction_keys.route_id
 AND waiting_metrics.direction_id IS NOT DISTINCT FROM direction_keys.direction_id
LEFT JOIN runtime_metrics
  ON runtime_metrics.route_id = direction_keys.route_id
 AND runtime_metrics.direction_id IS NOT DISTINCT FROM direction_keys.direction_id
LEFT JOIN matched_coverage
  ON matched_coverage.route_id = direction_keys.route_id
 AND matched_coverage.direction_id IS NOT DISTINCT FROM direction_keys.direction_id
LEFT JOIN unmatched_coverage
  ON unmatched_coverage.route_id = direction_keys.route_id
 AND unmatched_coverage.direction_id IS NOT DISTINCT FROM direction_keys.direction_id;

CREATE INDEX route_direction_summary_route_idx
    ON marts.route_direction_summary (route_id, direction_id);

CREATE INDEX route_direction_summary_loss_idx
    ON marts.route_direction_summary (typical_trip_loss_minutes DESC NULLS LAST);

CREATE TABLE marts.route_hour_summary AS
WITH waiting_metrics AS (
    SELECT
        route_id,
        direction_id,
        hour_local,
        ROUND(
            GREATEST(
                0::NUMERIC,
                (
                    SUM(observed_headway_secs * observed_headway_secs)
                    / (2 * SUM(observed_headway_secs) * 60.0)
                )
                - (
                    SUM(scheduled_headway_secs * scheduled_headway_secs)
                    / (2 * SUM(scheduled_headway_secs) * 60.0)
                )
            ),
            6
        ) AS waiting_loss_minutes,
        COUNT(*) AS matched_headway_interval_count
    FROM tmp_metric_headway_intervals
    GROUP BY route_id, direction_id, hour_local
),
runtime_metrics AS (
    SELECT
        route_id,
        direction_id,
        trip_start_hour_local AS hour_local,
        ROUND(
            (
                PERCENTILE_CONT(0.5)
                WITHIN GROUP (ORDER BY in_vehicle_loss_minutes)
            )::NUMERIC,
            6
        ) AS in_vehicle_loss_minutes,
        COUNT(*) AS matched_full_trip_count
    FROM tmp_metric_full_trip_metrics
    GROUP BY route_id, direction_id, trip_start_hour_local
),
matched_coverage AS (
    SELECT
        route_id,
        direction_id,
        hour_local,
        COUNT(*) AS matched_observed_stop_event_count
    FROM tmp_metric_matched_stop_event_coverage
    GROUP BY route_id, direction_id, hour_local
),
unmatched_coverage AS (
    SELECT
        route_id,
        direction_id,
        hour_local,
        COUNT(*) AS resolved_unmatched_observation_count
    FROM tmp_metric_unmatched_resolved
    GROUP BY route_id, direction_id, hour_local
)
SELECT
    hour_keys.route_id,
    COALESCE(routes.route_long_name, routes.route_short_name, hour_keys.route_id) AS route_name,
    routes.route_short_name,
    routes.route_long_name,
    hour_keys.direction_id,
    direction_labels.direction_label,
    hour_keys.hour_local,
    CASE
        WHEN waiting_metrics.waiting_loss_minutes IS NOT NULL
         AND runtime_metrics.in_vehicle_loss_minutes IS NOT NULL
        THEN ROUND(
            waiting_metrics.waiting_loss_minutes
            + runtime_metrics.in_vehicle_loss_minutes,
            6
        )
        ELSE NULL
    END AS typical_trip_loss_minutes,
    waiting_metrics.waiting_loss_minutes,
    runtime_metrics.in_vehicle_loss_minutes,
    COALESCE(matched_coverage.matched_observed_stop_event_count, 0)
        AS matched_observed_stop_event_count,
    COALESCE(unmatched_coverage.resolved_unmatched_observation_count, 0)
        AS resolved_unmatched_observation_count,
    COALESCE(waiting_metrics.matched_headway_interval_count, 0)
        AS matched_headway_interval_count,
    COALESCE(runtime_metrics.matched_full_trip_count, 0)
        AS matched_full_trip_count,
    CURRENT_TIMESTAMP AS metric_updated_at
FROM tmp_metric_route_hour_keys AS hour_keys
JOIN canonical.scheduled_routes AS routes
  ON routes.route_id = hour_keys.route_id
LEFT JOIN tmp_metric_direction_labels AS direction_labels
  ON direction_labels.route_id = hour_keys.route_id
 AND direction_labels.direction_id IS NOT DISTINCT FROM hour_keys.direction_id
LEFT JOIN waiting_metrics
  ON waiting_metrics.route_id = hour_keys.route_id
 AND waiting_metrics.direction_id IS NOT DISTINCT FROM hour_keys.direction_id
 AND waiting_metrics.hour_local = hour_keys.hour_local
LEFT JOIN runtime_metrics
  ON runtime_metrics.route_id = hour_keys.route_id
 AND runtime_metrics.direction_id IS NOT DISTINCT FROM hour_keys.direction_id
 AND runtime_metrics.hour_local = hour_keys.hour_local
LEFT JOIN matched_coverage
  ON matched_coverage.route_id = hour_keys.route_id
 AND matched_coverage.direction_id IS NOT DISTINCT FROM hour_keys.direction_id
 AND matched_coverage.hour_local = hour_keys.hour_local
LEFT JOIN unmatched_coverage
  ON unmatched_coverage.route_id = hour_keys.route_id
 AND unmatched_coverage.direction_id IS NOT DISTINCT FROM hour_keys.direction_id
 AND unmatched_coverage.hour_local = hour_keys.hour_local;

CREATE INDEX route_hour_summary_route_idx
    ON marts.route_hour_summary (route_id, direction_id, hour_local);

CREATE INDEX route_hour_summary_loss_idx
    ON marts.route_hour_summary (typical_trip_loss_minutes DESC NULLS LAST);
