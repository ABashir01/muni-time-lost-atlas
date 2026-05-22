{{ config(
    materialized=var('observed_canonical_materialization', 'view'),
    tags=['observed'],
    post_hook=(
        [
            "create index if not exists observed_stop_events_service_trip_stop_idx on {{ this }} (service_date, trip_id, stop_sequence, stop_id)"
        ] if var('observed_canonical_materialization', 'view') == 'table' and var('performance_indexing', false) else []
    )
) }}

select
    service_date,
    trip_id,
    route_id,
    service_id,
    observed_stop_id as stop_id,
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
from {{ ref('observed_stop_event_join_audit') }}
where join_status = 'matched_exact'
