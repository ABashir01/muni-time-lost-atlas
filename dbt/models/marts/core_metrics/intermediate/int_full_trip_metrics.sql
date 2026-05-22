{{ config(materialized=var('metrics_intermediate_materialization', 'ephemeral'), tags=['metrics']) }}

select
    terminals.route_id,
    terminals.direction_id,
    terminals.trip_headsign,
    terminals.service_date,
    terminals.trip_id,
    terminals.trip_start_hour_local,
    extract(
        epoch from (
            observed_last.observed_arrival_ts
            - observed_first.observed_arrival_ts
        )
    )::numeric as observed_runtime_secs,
    (terminals.last_arrival_time_secs - terminals.first_arrival_time_secs)::numeric
        as scheduled_runtime_secs,
    round(
        greatest(
            0::numeric,
            (
                extract(
                    epoch from (
                        observed_last.observed_arrival_ts
                        - observed_first.observed_arrival_ts
                    )
                )::numeric
                - (terminals.last_arrival_time_secs - terminals.first_arrival_time_secs)::numeric
            ) / 60.0
        ),
        6
    ) as in_vehicle_loss_minutes
from {{ ref('int_scheduled_trip_terminals') }} as terminals
join {{ ref('observed_stop_events') }} as observed_first
  on observed_first.trip_id = terminals.trip_id
 and observed_first.service_date = terminals.service_date
 and observed_first.stop_sequence = terminals.first_stop_sequence
 and observed_first.stop_id = terminals.first_stop_id
join {{ ref('observed_stop_events') }} as observed_last
  on observed_last.trip_id = terminals.trip_id
 and observed_last.service_date = terminals.service_date
 and observed_last.stop_sequence = terminals.last_stop_sequence
 and observed_last.stop_id = terminals.last_stop_id
where terminals.first_scheduled_arrival_ts is not null
  and terminals.last_scheduled_arrival_ts is not null
  and terminals.last_arrival_time_secs is not null
  and terminals.first_arrival_time_secs is not null
