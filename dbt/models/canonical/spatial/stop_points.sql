{{ config(materialized='table', tags=['gis']) }}

select
    stop_id,
    stop_name,
    stop_lat,
    stop_lon,
    st_setsrid(st_makepoint(stop_lon, stop_lat), 4326)::geometry(Point, 4326) as geom,
    source_system,
    feed_scope,
    operator_id,
    snapshot_label
from {{ ref('scheduled_stops') }}
where stop_lat is not null
  and stop_lon is not null
