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
)

select
    stop_times.trip_id,
    nullif(stop_times.arrival_time, '') as arrival_time_text,
    nullif(stop_times.departure_time, '') as departure_time_text,
    stop_times.stop_id,
    nullif(stop_times.stop_sequence, '')::integer as stop_sequence,
    nullif(stop_times.shape_dist_traveled, '')::double precision as shape_dist_traveled,
    case
        when nullif(stop_times.arrival_time, '') is null then null
        else (
            split_part(stop_times.arrival_time, ':', 1)::integer * 3600
            + split_part(stop_times.arrival_time, ':', 2)::integer * 60
            + split_part(stop_times.arrival_time, ':', 3)::integer
        )
    end as arrival_time_secs,
    case
        when nullif(stop_times.departure_time, '') is null then null
        else (
            split_part(stop_times.departure_time, ':', 1)::integer * 3600
            + split_part(stop_times.departure_time, ':', 2)::integer * 60
            + split_part(stop_times.departure_time, ':', 3)::integer
        )
    end as departure_time_secs,
    stop_times.source_system,
    stop_times.feed_scope,
    nullif(stop_times.operator_id, '') as operator_id,
    stop_times.snapshot_label
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
