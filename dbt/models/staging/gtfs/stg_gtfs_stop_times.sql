{{ config(materialized='table', tags=['scheduled']) }}

select
    trip_id,
    nullif(arrival_time, '') as arrival_time_text,
    nullif(departure_time, '') as departure_time_text,
    stop_id,
    nullif(stop_sequence, '')::integer as stop_sequence,
    nullif(shape_dist_traveled, '')::double precision as shape_dist_traveled,
    case
        when nullif(arrival_time, '') is null then null
        else (
            split_part(arrival_time, ':', 1)::integer * 3600
            + split_part(arrival_time, ':', 2)::integer * 60
            + split_part(arrival_time, ':', 3)::integer
        )
    end as arrival_time_secs,
    case
        when nullif(departure_time, '') is null then null
        else (
            split_part(departure_time, ':', 1)::integer * 3600
            + split_part(departure_time, ':', 2)::integer * 60
            + split_part(departure_time, ':', 3)::integer
        )
    end as departure_time_secs,
    source_system,
    feed_scope,
    nullif(operator_id, '') as operator_id,
    snapshot_label
from {{ source('raw', 'gtfs_stop_times') }}
where feed_scope = 'operator_active'
  and snapshot_label = ({{ latest_active_snapshot_subquery() }})
