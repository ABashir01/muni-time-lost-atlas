{{ config(materialized='table', tags=['scheduled']) }}

with selected_snapshot as (
    {{ target_gtfs_snapshot_subquery() }}
)

select distinct
    routes.route_id,
    nullif(routes.agency_id, '') as agency_id,
    nullif(routes.route_short_name, '') as route_short_name,
    nullif(routes.route_long_name, '') as route_long_name,
    nullif(routes.route_type, '')::integer as route_type,
    nullif(routes.route_color, '') as route_color,
    nullif(routes.route_text_color, '') as route_text_color,
    routes.source_system,
    routes.feed_scope,
    nullif(routes.operator_id, '') as operator_id,
    routes.snapshot_label
from {{ source('raw', 'gtfs_routes') }} as routes
cross join selected_snapshot
where routes.feed_scope = '{{ target_gtfs_feed_scope() }}'
  and routes.snapshot_label = selected_snapshot.snapshot_label
  and (
      '{{ target_gtfs_feed_scope() }}' != 'regional_historic'
      or routes.agency_id = '{{ historic_agency_id() }}'
  )
