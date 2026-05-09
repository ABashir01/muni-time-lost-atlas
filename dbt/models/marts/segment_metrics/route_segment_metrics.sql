{{ config(materialized='table', tags=['metrics', 'gis']) }}

with observed_segment_pairs as (
    select
        route_id,
        direction_id,
        shape_id,
        trip_id,
        service_date,
        trip_headsign,
        stop_sequence as segment_sequence,
        stop_id as from_stop_id,
        lead(stop_sequence) over (
            partition by trip_id, service_date
            order by stop_sequence
        ) as to_stop_sequence,
        lead(stop_id) over (
            partition by trip_id, service_date
            order by stop_sequence
        ) as to_stop_id,
        observed_arrival_ts as from_observed_arrival_ts,
        lead(observed_arrival_ts) over (
            partition by trip_id, service_date
            order by stop_sequence
        ) as to_observed_arrival_ts,
        scheduled_arrival_time_secs as from_scheduled_arrival_time_secs,
        lead(scheduled_arrival_time_secs) over (
            partition by trip_id, service_date
            order by stop_sequence
        ) as to_scheduled_arrival_time_secs
    from {{ ref('observed_stop_events') }}
),
trip_segment_metrics as (
    select
        route_id,
        direction_id,
        shape_id,
        trip_id,
        service_date,
        segment_sequence,
        from_stop_id,
        to_stop_id,
        round(
            greatest(
                0::numeric,
                (
                    extract(
                        epoch from (to_observed_arrival_ts - from_observed_arrival_ts)
                    )::numeric
                    - (to_scheduled_arrival_time_secs - from_scheduled_arrival_time_secs)::numeric
                ) / 60.0
            ),
            6
        ) as segment_in_vehicle_loss_minutes
    from observed_segment_pairs
    where to_stop_id is not null
      and to_stop_sequence = segment_sequence + 1
      and from_observed_arrival_ts is not null
      and to_observed_arrival_ts is not null
      and from_scheduled_arrival_time_secs is not null
      and to_scheduled_arrival_time_secs is not null
)
select
    segments.route_id,
    coalesce(routes.route_long_name, routes.route_short_name, segments.route_id) as route_name,
    routes.route_short_name,
    routes.route_long_name,
    segments.direction_id,
    segments.direction_label,
    segments.shape_id,
    'adjacent_stop_pair'::text as segment_strategy,
    'all_day'::text as window_key,
    segments.segment_sequence,
    segments.from_stop_id,
    segments.from_stop_name,
    segments.to_stop_id,
    segments.to_stop_name,
    segments.segment_label,
    segments.scheduled_segment_minutes,
    round(
        (
            percentile_cont(0.5)
            within group (order by trip_segment_metrics.segment_in_vehicle_loss_minutes)
        )::numeric,
        6
    ) as segment_in_vehicle_loss_minutes,
    count(trip_segment_metrics.trip_id) as matched_trip_segment_count,
    current_timestamp as metric_updated_at
from {{ ref('route_stop_segments') }} as segments
join {{ ref('scheduled_routes') }} as routes
  on routes.route_id = segments.route_id
left join trip_segment_metrics
  on trip_segment_metrics.route_id = segments.route_id
 and trip_segment_metrics.direction_id is not distinct from segments.direction_id
 and trip_segment_metrics.shape_id = segments.shape_id
 and trip_segment_metrics.segment_sequence = segments.segment_sequence
 and trip_segment_metrics.from_stop_id = segments.from_stop_id
 and trip_segment_metrics.to_stop_id = segments.to_stop_id
group by
    segments.route_id,
    route_name,
    routes.route_short_name,
    routes.route_long_name,
    segments.direction_id,
    segments.direction_label,
    segments.shape_id,
    segments.segment_sequence,
    segments.from_stop_id,
    segments.from_stop_name,
    segments.to_stop_id,
    segments.to_stop_name,
    segments.segment_label,
    segments.scheduled_segment_minutes
