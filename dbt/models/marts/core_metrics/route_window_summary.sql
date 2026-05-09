{{ config(materialized='table', tags=['metrics']) }}

with waiting_metrics as (
    select
        route_id,
        round(
            greatest(
                0::numeric,
                (
                    sum(observed_headway_secs * observed_headway_secs)
                    / (2 * sum(observed_headway_secs) * 60.0)
                )
                - (
                    sum(scheduled_headway_secs * scheduled_headway_secs)
                    / (2 * sum(scheduled_headway_secs) * 60.0)
                )
            ),
            6
        ) as waiting_loss_minutes,
        count(*) as matched_headway_interval_count
    from {{ ref('int_headway_intervals') }}
    group by route_id
),
runtime_metrics as (
    select
        route_id,
        round(
            (
                percentile_cont(0.5)
                within group (order by in_vehicle_loss_minutes)
            )::numeric,
            6
        ) as in_vehicle_loss_minutes,
        count(*) as matched_full_trip_count
    from {{ ref('int_full_trip_metrics') }}
    group by route_id
),
matched_coverage as (
    select
        route_id,
        count(*) as matched_observed_stop_event_count
    from {{ ref('int_matched_stop_event_coverage') }}
    group by route_id
),
unmatched_coverage as (
    select
        route_id,
        count(*) as resolved_unmatched_observation_count
    from {{ ref('int_unmatched_resolved') }}
    group by route_id
)
select
    route_keys.route_id,
    coalesce(routes.route_long_name, routes.route_short_name, route_keys.route_id) as route_name,
    routes.route_short_name,
    routes.route_long_name,
    'all_day'::text as window_key,
    case
        when waiting_metrics.waiting_loss_minutes is not null
         and runtime_metrics.in_vehicle_loss_minutes is not null
        then round(
            waiting_metrics.waiting_loss_minutes
            + runtime_metrics.in_vehicle_loss_minutes,
            6
        )
        else null
    end as typical_trip_loss_minutes,
    waiting_metrics.waiting_loss_minutes,
    runtime_metrics.in_vehicle_loss_minutes,
    worst_segment.segment_label as worst_segment_label,
    coalesce(matched_coverage.matched_observed_stop_event_count, 0)
        as matched_observed_stop_event_count,
    coalesce(unmatched_coverage.resolved_unmatched_observation_count, 0)
        as resolved_unmatched_observation_count,
    coalesce(waiting_metrics.matched_headway_interval_count, 0)
        as matched_headway_interval_count,
    coalesce(runtime_metrics.matched_full_trip_count, 0)
        as matched_full_trip_count,
    current_timestamp as metric_updated_at
from {{ ref('int_route_keys') }} as route_keys
join {{ ref('scheduled_routes') }} as routes
  on routes.route_id = route_keys.route_id
left join lateral (
    select segment_label
    from {{ ref('route_segment_metrics') }} as route_segment_metrics
    where route_segment_metrics.route_id = route_keys.route_id
      and route_segment_metrics.window_key = 'all_day'
    order by
        route_segment_metrics.segment_in_vehicle_loss_minutes desc nulls last,
        route_segment_metrics.direction_id,
        route_segment_metrics.segment_sequence
    limit 1
) as worst_segment on true
left join waiting_metrics
  on waiting_metrics.route_id = route_keys.route_id
left join runtime_metrics
  on runtime_metrics.route_id = route_keys.route_id
left join matched_coverage
  on matched_coverage.route_id = route_keys.route_id
left join unmatched_coverage
  on unmatched_coverage.route_id = route_keys.route_id
