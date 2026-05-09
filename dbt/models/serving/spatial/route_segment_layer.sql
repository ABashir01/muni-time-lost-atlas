{{ config(materialized='table', tags=['serving', 'gis']) }}

select
    metrics.route_id,
    metrics.route_name,
    metrics.route_short_name,
    metrics.route_long_name,
    metrics.direction_id,
    metrics.direction_label,
    metrics.shape_id,
    metrics.segment_strategy,
    metrics.window_key,
    metrics.segment_sequence,
    metrics.from_stop_id,
    metrics.from_stop_name,
    metrics.to_stop_id,
    metrics.to_stop_name,
    metrics.segment_label,
    metrics.scheduled_segment_minutes,
    metrics.segment_in_vehicle_loss_minutes,
    metrics.matched_trip_segment_count,
    metrics.metric_updated_at,
    segments.geom
from {{ ref('route_segment_metrics') }} as metrics
join {{ ref('route_stop_segments') }} as segments
  on segments.route_id = metrics.route_id
 and segments.direction_id is not distinct from metrics.direction_id
 and segments.shape_id = metrics.shape_id
 and segments.segment_sequence = metrics.segment_sequence
 and segments.from_stop_id = metrics.from_stop_id
 and segments.to_stop_id = metrics.to_stop_id
