{{ config(materialized='table', tags=['metrics', 'gis']) }}

with aggregated_waiting as (
    select
        route_id,
        direction_id,
        first_stop_id as stop_id,
        (
            sum(observed_headway_secs * observed_headway_secs)
            / (2 * sum(observed_headway_secs) * 60.0)
        )::numeric as observed_effective_wait_minutes_raw,
        (
            sum(scheduled_headway_secs * scheduled_headway_secs)
            / (2 * sum(scheduled_headway_secs) * 60.0)
        )::numeric as scheduled_effective_wait_minutes_raw,
        count(*) as matched_headway_interval_count
    from {{ ref('int_headway_intervals') }}
    group by route_id, direction_id, first_stop_id
)
select
    aggregated_waiting.route_id,
    coalesce(routes.route_long_name, routes.route_short_name, aggregated_waiting.route_id) as route_name,
    routes.route_short_name,
    routes.route_long_name,
    aggregated_waiting.direction_id,
    direction_labels.direction_label,
    aggregated_waiting.stop_id,
    stops.stop_name,
    case
        when direction_labels.direction_label is not null
        then concat(stops.stop_name, ' (', direction_labels.direction_label, ')')
        when aggregated_waiting.direction_id is not null
        then concat(stops.stop_name, ' (Direction ', aggregated_waiting.direction_id::text, ')')
        else stops.stop_name
    end as stop_wait_label,
    'all_day'::text as window_key,
    'first_stop_exact_match'::text as stop_wait_strategy,
    round(
        aggregated_waiting.scheduled_effective_wait_minutes_raw,
        6
    ) as scheduled_effective_wait_minutes,
    round(
        aggregated_waiting.observed_effective_wait_minutes_raw,
        6
    ) as observed_effective_wait_minutes,
    round(
        greatest(
            0::numeric,
            aggregated_waiting.observed_effective_wait_minutes_raw
            - aggregated_waiting.scheduled_effective_wait_minutes_raw
        ),
        6
    ) as waiting_loss_minutes,
    aggregated_waiting.matched_headway_interval_count,
    current_timestamp as metric_updated_at
from aggregated_waiting
join {{ ref('scheduled_routes') }} as routes
  on routes.route_id = aggregated_waiting.route_id
join {{ ref('scheduled_stops') }} as stops
  on stops.stop_id = aggregated_waiting.stop_id
left join {{ ref('int_direction_labels') }} as direction_labels
  on direction_labels.route_id = aggregated_waiting.route_id
 and direction_labels.direction_id is not distinct from aggregated_waiting.direction_id
