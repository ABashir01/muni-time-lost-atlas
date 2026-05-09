{{ config(materialized='ephemeral', tags=['metrics']) }}

select
    current_trip.route_id,
    current_trip.direction_id,
    current_trip.trip_headsign,
    current_trip.service_date,
    current_trip.first_stop_id,
    extract(
        hour from (
            current_trip.first_scheduled_arrival_ts
            + (
                next_trip.first_scheduled_arrival_ts
                - current_trip.first_scheduled_arrival_ts
            ) / 2
        ) at time zone 'America/Los_Angeles'
    )::integer as hour_local,
    extract(
        epoch from (
            next_trip.first_scheduled_arrival_ts
            - current_trip.first_scheduled_arrival_ts
        )
    )::numeric as scheduled_headway_secs,
    extract(
        epoch from (
            next_trip.observed_first_arrival_ts
            - current_trip.observed_first_arrival_ts
        )
    )::numeric as observed_headway_secs
from {{ ref('int_matched_first_stop_events') }} as current_trip
join {{ ref('int_matched_first_stop_events') }} as next_trip
  on next_trip.route_id = current_trip.route_id
 and next_trip.direction_id is not distinct from current_trip.direction_id
 and next_trip.first_stop_id = current_trip.first_stop_id
 and next_trip.service_date = current_trip.service_date
 and next_trip.first_stop_trip_order = current_trip.first_stop_trip_order + 1
where extract(
        epoch from (
            next_trip.first_scheduled_arrival_ts
            - current_trip.first_scheduled_arrival_ts
        )
    ) > 0
  and extract(
        epoch from (
            next_trip.observed_first_arrival_ts
            - current_trip.observed_first_arrival_ts
        )
    ) > 0
