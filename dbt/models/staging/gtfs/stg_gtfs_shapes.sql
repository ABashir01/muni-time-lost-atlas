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
filtered_shapes as (
    select distinct nullif(shape_id, '') as shape_id
    from {{ source('raw', 'gtfs_trips') }} as trips
    cross join selected_snapshot
    where trips.feed_scope = '{{ target_gtfs_feed_scope() }}'
      and trips.snapshot_label = selected_snapshot.snapshot_label
      and nullif(trips.shape_id, '') is not null
      and (
          '{{ target_gtfs_feed_scope() }}' != 'regional_historic'
          or exists (
              select 1
              from filtered_routes
              where filtered_routes.route_id = trips.route_id
          )
      )
)

select
    shapes.shape_id,
    nullif(shapes.shape_pt_lat, '')::double precision as shape_pt_lat,
    nullif(shapes.shape_pt_lon, '')::double precision as shape_pt_lon,
    nullif(shapes.shape_pt_sequence, '')::integer as shape_pt_sequence,
    nullif(shapes.shape_dist_traveled, '')::double precision as shape_dist_traveled,
    shapes.source_system,
    shapes.feed_scope,
    nullif(shapes.operator_id, '') as operator_id,
    shapes.snapshot_label
from {{ source('raw', 'gtfs_shapes') }} as shapes
cross join selected_snapshot
where shapes.feed_scope = '{{ target_gtfs_feed_scope() }}'
  and shapes.snapshot_label = selected_snapshot.snapshot_label
  and (
      '{{ target_gtfs_feed_scope() }}' != 'regional_historic'
      or exists (
          select 1
          from filtered_shapes
          where filtered_shapes.shape_id = shapes.shape_id
      )
  )
