{{ config(materialized='table', tags=['gis']) }}

with distinct_shapes as (
    select distinct
        route_id,
        direction_id,
        shape_id,
        trip_headsign,
        source_system,
        feed_scope,
        operator_id,
        snapshot_label
    from {{ ref('scheduled_trips') }}
    where shape_id is not null
),
shape_points as (
    select
        distinct_shapes.route_id,
        distinct_shapes.direction_id,
        distinct_shapes.shape_id,
        distinct_shapes.trip_headsign,
        shapes.shape_pt_sequence,
        shapes.shape_pt_lat,
        shapes.shape_pt_lon,
        shapes.shape_dist_traveled,
        distinct_shapes.source_system,
        distinct_shapes.feed_scope,
        distinct_shapes.operator_id,
        distinct_shapes.snapshot_label
    from distinct_shapes
    join {{ ref('stg_gtfs_shapes') }} as shapes
      on shapes.shape_id = distinct_shapes.shape_id
    where shapes.shape_pt_lat is not null
      and shapes.shape_pt_lon is not null
)
select
    route_id,
    direction_id,
    shape_id,
    min(trip_headsign) as direction_label,
    st_makeline(
        st_setsrid(st_makepoint(shape_pt_lon, shape_pt_lat), 4326)
        order by shape_pt_sequence
    )::geometry(LineString, 4326) as geom,
    max(shape_dist_traveled) as max_shape_dist_traveled,
    min(source_system) as source_system,
    min(feed_scope) as feed_scope,
    min(operator_id) as operator_id,
    min(snapshot_label) as snapshot_label
from shape_points
group by route_id, direction_id, shape_id
