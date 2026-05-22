{{ config(materialized='table', tags=['scheduled']) }}

with selected_snapshot as (
    {{ target_gtfs_snapshot_subquery() }}
),
filtered_routes as (
    select route_id
    from {{ source('raw', 'gtfs_routes') }} as routes
    cross join selected_snapshot
    where routes.feed_scope = '{{ target_gtfs_feed_scope() }}'
      and routes.snapshot_label = selected_snapshot.snapshot_label
      and (
          '{{ target_gtfs_feed_scope() }}' != 'regional_historic'
          or routes.agency_id = '{{ historic_agency_id() }}'
      )
)

select distinct
    trips.route_id,
    trips.service_id,
    trips.trip_id,
    nullif(trips.trip_headsign, '') as trip_headsign,
    nullif(trips.direction_id, '')::integer as direction_id,
    nullif(trips.shape_id, '') as shape_id,
    trips.source_system,
    trips.feed_scope,
    nullif(trips.operator_id, '') as operator_id,
    trips.snapshot_label
from {{ source('raw', 'gtfs_trips') }} as trips
cross join selected_snapshot
where trips.feed_scope = '{{ target_gtfs_feed_scope() }}'
  and trips.snapshot_label = selected_snapshot.snapshot_label
  and (
      '{{ target_gtfs_feed_scope() }}' != 'regional_historic'
      or exists (
          select 1
          from filtered_routes
          where filtered_routes.route_id = trips.route_id
      )
  )
