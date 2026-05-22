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
),
filtered_trips as (
    select trip_id
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
),
filtered_stop_ids as (
    select distinct stop_id
    from {{ source('raw', 'gtfs_stop_times') }} as stop_times
    cross join selected_snapshot
    where stop_times.feed_scope = '{{ target_gtfs_feed_scope() }}'
      and stop_times.snapshot_label = selected_snapshot.snapshot_label
      and (
          '{{ target_gtfs_feed_scope() }}' != 'regional_historic'
          or exists (
              select 1
              from filtered_trips
              where filtered_trips.trip_id = stop_times.trip_id
          )
      )
)

select distinct
    stops.stop_id,
    nullif(stops.stop_name, '') as stop_name,
    nullif(stops.stop_lat, '')::double precision as stop_lat,
    nullif(stops.stop_lon, '')::double precision as stop_lon,
    stops.source_system,
    stops.feed_scope,
    nullif(stops.operator_id, '') as operator_id,
    stops.snapshot_label
from {{ source('raw', 'gtfs_stops') }} as stops
cross join selected_snapshot
where stops.feed_scope = '{{ target_gtfs_feed_scope() }}'
  and stops.snapshot_label = selected_snapshot.snapshot_label
  and (
      '{{ target_gtfs_feed_scope() }}' != 'regional_historic'
      or exists (
          select 1
          from filtered_stop_ids
          where filtered_stop_ids.stop_id = stops.stop_id
      )
  )
