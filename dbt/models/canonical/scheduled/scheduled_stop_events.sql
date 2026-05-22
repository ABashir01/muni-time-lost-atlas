{{ config(
    materialized='table',
    tags=['scheduled'],
    post_hook=(
        [
            "create index if not exists scheduled_stop_events_service_trip_stop_idx on {{ this }} (service_date, trip_id, stop_sequence, stop_id)"
        ] if var('performance_indexing', false) else []
    )
) }}

select
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
from {{ ref('scheduled_trips') }} as trips
join {{ ref('service_dates') }} as service_dates
  on trips.service_id = service_dates.service_id
join {{ ref('stg_gtfs_stop_times') }} as stop_times
  on trips.trip_id = stop_times.trip_id
