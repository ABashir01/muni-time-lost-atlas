{{ config(materialized='ephemeral', tags=['metrics']) }}

with trip_bounds as (
    select
        trip_id,
        service_date,
        min(stop_sequence) as first_stop_sequence,
        max(stop_sequence) as last_stop_sequence
    from {{ ref('scheduled_stop_events') }}
    group by trip_id, service_date
)
select
    first_stop.trip_id,
    first_stop.route_id,
    first_stop.service_id,
    first_stop.service_date,
    first_stop.direction_id,
    first_stop.trip_headsign,
    first_stop.stop_id as first_stop_id,
    last_stop.stop_id as last_stop_id,
    first_stop.stop_sequence as first_stop_sequence,
    last_stop.stop_sequence as last_stop_sequence,
    first_stop.arrival_time_secs as first_arrival_time_secs,
    last_stop.arrival_time_secs as last_arrival_time_secs,
    case
        when first_stop.arrival_time_secs is null then null
        else (
            first_stop.service_date::timestamp
            + first_stop.arrival_time_secs * interval '1 second'
        ) at time zone 'America/Los_Angeles'
    end as first_scheduled_arrival_ts,
    case
        when last_stop.arrival_time_secs is null then null
        else (
            last_stop.service_date::timestamp
            + last_stop.arrival_time_secs * interval '1 second'
        ) at time zone 'America/Los_Angeles'
    end as last_scheduled_arrival_ts,
    extract(
        hour from (
            first_stop.service_date::timestamp
            + first_stop.arrival_time_secs * interval '1 second'
        )
    )::integer as trip_start_hour_local,
    row_number() over (
        partition by
            first_stop.route_id,
            first_stop.direction_id,
            first_stop.stop_id,
            first_stop.service_date
        order by first_stop.arrival_time_secs, first_stop.trip_id
    ) as first_stop_trip_order
from trip_bounds
join {{ ref('scheduled_stop_events') }} as first_stop
  on first_stop.trip_id = trip_bounds.trip_id
 and first_stop.service_date = trip_bounds.service_date
 and first_stop.stop_sequence = trip_bounds.first_stop_sequence
join {{ ref('scheduled_stop_events') }} as last_stop
  on last_stop.trip_id = trip_bounds.trip_id
 and last_stop.service_date = trip_bounds.service_date
 and last_stop.stop_sequence = trip_bounds.last_stop_sequence
