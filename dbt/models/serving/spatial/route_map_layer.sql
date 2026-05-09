{{ config(materialized='table', tags=['serving', 'gis']) }}

with route_lines as (
    select
        route_id,
        st_linemerge(st_union(geom)) as geom
    from {{ ref('route_geometries') }}
    group by route_id
)
select
    summaries.route_id,
    summaries.route_name,
    summaries.route_short_name,
    summaries.route_long_name,
    summaries.window_key,
    summaries.typical_trip_loss_minutes,
    summaries.waiting_loss_minutes,
    summaries.in_vehicle_loss_minutes,
    summaries.worst_segment_label,
    summaries.metric_updated_at,
    route_lines.geom
from {{ ref('route_window_summary') }} as summaries
join route_lines
  on route_lines.route_id = summaries.route_id
