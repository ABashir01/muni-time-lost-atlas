{{ config(materialized='table', tags=['gis']) }}

with trip_stop_pairs as (
    select
        trips.route_id,
        trips.direction_id,
        trips.shape_id,
        trips.trip_id,
        trips.trip_headsign,
        stop_times.stop_sequence as from_stop_sequence,
        stop_times.stop_id as from_stop_id,
        from_stops.stop_name as from_stop_name,
        stop_times.shape_dist_traveled as from_shape_dist_traveled,
        stop_times.arrival_time_secs as from_arrival_time_secs,
        lead(stop_times.stop_sequence) over (
            partition by trips.trip_id
            order by stop_times.stop_sequence
        ) as to_stop_sequence,
        lead(stop_times.stop_id) over (
            partition by trips.trip_id
            order by stop_times.stop_sequence
        ) as to_stop_id,
        lead(stop_times.shape_dist_traveled) over (
            partition by trips.trip_id
            order by stop_times.stop_sequence
        ) as to_shape_dist_traveled,
        lead(stop_times.arrival_time_secs) over (
            partition by trips.trip_id
            order by stop_times.stop_sequence
        ) as to_arrival_time_secs,
        trips.source_system,
        trips.feed_scope,
        trips.operator_id,
        trips.snapshot_label
    from {{ ref('scheduled_trips') }} as trips
    join {{ ref('stg_gtfs_stop_times') }} as stop_times
      on stop_times.trip_id = trips.trip_id
    join {{ ref('scheduled_stops') }} as from_stops
      on from_stops.stop_id = stop_times.stop_id
),
adjacent_pairs as (
    select
        trip_stop_pairs.*,
        to_stops.stop_name as to_stop_name
    from trip_stop_pairs
    join {{ ref('scheduled_stops') }} as to_stops
      on to_stops.stop_id = trip_stop_pairs.to_stop_id
    where trip_stop_pairs.to_stop_id is not null
      and trip_stop_pairs.to_stop_sequence = trip_stop_pairs.from_stop_sequence + 1
),
deduplicated_pairs as (
    select
        adjacent_pairs.*,
        row_number() over (
            partition by
                route_id,
                direction_id,
                shape_id,
                from_stop_sequence,
                from_stop_id,
                to_stop_id
            order by trip_id
        ) as pair_rank
    from adjacent_pairs
),
segment_geometry_inputs as (
    select
        pairs.route_id,
        pairs.direction_id,
        pairs.shape_id,
        pairs.trip_id,
        pairs.trip_headsign,
        pairs.from_stop_sequence,
        pairs.from_stop_id,
        pairs.from_stop_name,
        pairs.to_stop_id,
        pairs.to_stop_name,
        pairs.from_arrival_time_secs,
        pairs.to_arrival_time_secs,
        pairs.from_shape_dist_traveled,
        pairs.to_shape_dist_traveled,
        pairs.source_system,
        pairs.feed_scope,
        pairs.operator_id,
        pairs.snapshot_label,
        route_geometries.geom as route_geom,
        route_geometries.max_shape_dist_traveled,
        from_points.geom as from_point_geom,
        to_points.geom as to_point_geom,
        case
            when route_geometries.max_shape_dist_traveled is not null
             and route_geometries.max_shape_dist_traveled > 0
             and pairs.from_shape_dist_traveled is not null
             and pairs.to_shape_dist_traveled is not null
             and pairs.to_shape_dist_traveled > pairs.from_shape_dist_traveled
            then greatest(
                0::double precision,
                least(
                    1::double precision,
                    pairs.from_shape_dist_traveled / route_geometries.max_shape_dist_traveled
                )
            )
            else null
        end as start_fraction,
        case
            when route_geometries.max_shape_dist_traveled is not null
             and route_geometries.max_shape_dist_traveled > 0
             and pairs.from_shape_dist_traveled is not null
             and pairs.to_shape_dist_traveled is not null
             and pairs.to_shape_dist_traveled > pairs.from_shape_dist_traveled
            then greatest(
                0::double precision,
                least(
                    1::double precision,
                    pairs.to_shape_dist_traveled / route_geometries.max_shape_dist_traveled
                )
            )
            else null
        end as end_fraction
    from deduplicated_pairs as pairs
    join {{ ref('route_geometries') }} as route_geometries
      on route_geometries.route_id = pairs.route_id
     and route_geometries.direction_id is not distinct from pairs.direction_id
     and route_geometries.shape_id = pairs.shape_id
    join {{ ref('stop_points') }} as from_points
      on from_points.stop_id = pairs.from_stop_id
    join {{ ref('stop_points') }} as to_points
      on to_points.stop_id = pairs.to_stop_id
    where pairs.pair_rank = 1
)
select
    pairs.route_id,
    pairs.direction_id,
    pairs.shape_id,
    pairs.trip_id as representative_trip_id,
    pairs.trip_headsign as direction_label,
    pairs.from_stop_sequence as segment_sequence,
    pairs.from_stop_id,
    pairs.from_stop_name,
    pairs.to_stop_id,
    pairs.to_stop_name,
    concat(pairs.from_stop_name, ' -> ', pairs.to_stop_name) as segment_label,
    round(
        greatest(
            0::numeric,
            (pairs.to_arrival_time_secs - pairs.from_arrival_time_secs)::numeric / 60.0
        ),
        6
    ) as scheduled_segment_minutes,
    pairs.from_shape_dist_traveled,
    pairs.to_shape_dist_traveled,
    case
        when pairs.start_fraction is not null
         and pairs.end_fraction is not null
         and pairs.end_fraction > pairs.start_fraction
        then st_linesubstring(
            pairs.route_geom,
            pairs.start_fraction,
            pairs.end_fraction
        )::geometry(LineString, 4326)
        else st_makeline(pairs.from_point_geom, pairs.to_point_geom)::geometry(LineString, 4326)
    end as geom,
    pairs.source_system,
    pairs.feed_scope,
    pairs.operator_id,
    pairs.snapshot_label
from segment_geometry_inputs as pairs
