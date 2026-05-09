{{ config(materialized='table', tags=['scheduled']) }}

select distinct
    route_id,
    service_id,
    trip_id,
    nullif(trip_headsign, '') as trip_headsign,
    nullif(direction_id, '')::integer as direction_id,
    nullif(shape_id, '') as shape_id,
    source_system,
    feed_scope,
    nullif(operator_id, '') as operator_id,
    snapshot_label
from {{ source('raw', 'gtfs_trips') }}
where feed_scope = 'operator_active'
  and snapshot_label = ({{ latest_active_snapshot_subquery() }})
