{{ config(materialized='table', tags=['scheduled']) }}

select distinct
    route_id,
    nullif(agency_id, '') as agency_id,
    nullif(route_short_name, '') as route_short_name,
    nullif(route_long_name, '') as route_long_name,
    nullif(route_type, '')::integer as route_type,
    nullif(route_color, '') as route_color,
    nullif(route_text_color, '') as route_text_color,
    source_system,
    feed_scope,
    nullif(operator_id, '') as operator_id,
    snapshot_label
from {{ source('raw', 'gtfs_routes') }}
where feed_scope = 'operator_active'
  and snapshot_label = ({{ latest_active_snapshot_subquery() }})
