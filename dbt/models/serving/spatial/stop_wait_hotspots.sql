{{ config(materialized='table', tags=['serving', 'gis']) }}

select
    metrics.route_id,
    metrics.route_name,
    metrics.route_short_name,
    metrics.route_long_name,
    metrics.direction_id,
    metrics.direction_label,
    metrics.stop_id,
    metrics.stop_name,
    metrics.stop_wait_label,
    metrics.window_key,
    metrics.stop_wait_strategy,
    metrics.scheduled_effective_wait_minutes,
    metrics.observed_effective_wait_minutes,
    metrics.waiting_loss_minutes,
    metrics.matched_headway_interval_count,
    metrics.metric_updated_at,
    stops.geom
from {{ ref('stop_wait_metrics') }} as metrics
join {{ ref('stop_points') }} as stops
  on stops.stop_id = metrics.stop_id
