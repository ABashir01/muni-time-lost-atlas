{{ config(materialized='table', tags=['scheduled']) }}

select distinct
    stop_id,
    nullif(stop_name, '') as stop_name,
    nullif(stop_lat, '')::double precision as stop_lat,
    nullif(stop_lon, '')::double precision as stop_lon,
    source_system,
    feed_scope,
    nullif(operator_id, '') as operator_id,
    snapshot_label
from {{ source('raw', 'gtfs_stops') }}
where feed_scope = 'operator_active'
  and snapshot_label = ({{ latest_active_snapshot_subquery() }})
