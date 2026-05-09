{{ config(materialized='table', tags=['metrics']) }}

with waiting_metrics as (
    select
        route_id,
        direction_id,
        hour_local,
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
    group by route_id, direction_id, hour_local
),
runtime_metrics as (
    select
        route_id,
        direction_id,
        trip_start_hour_local as hour_local,
        round(
            (
                percentile_cont(0.5)
                within group (order by in_vehicle_loss_minutes)
            )::numeric,
            6
        ) as in_vehicle_loss_minutes,
        count(*) as matched_full_trip_count
    from {{ ref('int_full_trip_metrics') }}
    group by route_id, direction_id, trip_start_hour_local
),
matched_coverage as (
    select
        route_id,
        direction_id,
        hour_local,
        count(*) as matched_observed_stop_event_count
    from {{ ref('int_matched_stop_event_coverage') }}
    group by route_id, direction_id, hour_local
),
unmatched_coverage as (
    select
        route_id,
        direction_id,
        hour_local,
        count(*) as resolved_unmatched_observation_count
    from {{ ref('int_unmatched_resolved') }}
    group by route_id, direction_id, hour_local
)
select
    hour_keys.route_id,
    coalesce(routes.route_long_name, routes.route_short_name, hour_keys.route_id) as route_name,
    routes.route_short_name,
    routes.route_long_name,
    hour_keys.direction_id,
    direction_labels.direction_label,
    hour_keys.hour_local,
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
    coalesce(matched_coverage.matched_observed_stop_event_count, 0)
        as matched_observed_stop_event_count,
    coalesce(unmatched_coverage.resolved_unmatched_observation_count, 0)
        as resolved_unmatched_observation_count,
    coalesce(waiting_metrics.matched_headway_interval_count, 0)
        as matched_headway_interval_count,
    coalesce(runtime_metrics.matched_full_trip_count, 0)
        as matched_full_trip_count,
    current_timestamp as metric_updated_at
from {{ ref('int_route_hour_keys') }} as hour_keys
join {{ ref('scheduled_routes') }} as routes
  on routes.route_id = hour_keys.route_id
left join {{ ref('int_direction_labels') }} as direction_labels
  on direction_labels.route_id = hour_keys.route_id
 and direction_labels.direction_id is not distinct from hour_keys.direction_id
left join waiting_metrics
  on waiting_metrics.route_id = hour_keys.route_id
 and waiting_metrics.direction_id is not distinct from hour_keys.direction_id
 and waiting_metrics.hour_local = hour_keys.hour_local
left join runtime_metrics
  on runtime_metrics.route_id = hour_keys.route_id
 and runtime_metrics.direction_id is not distinct from hour_keys.direction_id
 and runtime_metrics.hour_local = hour_keys.hour_local
left join matched_coverage
  on matched_coverage.route_id = hour_keys.route_id
 and matched_coverage.direction_id is not distinct from hour_keys.direction_id
 and matched_coverage.hour_local = hour_keys.hour_local
left join unmatched_coverage
  on unmatched_coverage.route_id = hour_keys.route_id
 and unmatched_coverage.direction_id is not distinct from hour_keys.direction_id
 and unmatched_coverage.hour_local = hour_keys.hour_local
