{{ config(materialized='view', tags=['observed']) }}

with observed_base as (
    select
        observations.service_date,
        observations.trip_id,
        observations.stop_id,
        observations.stop_sequence,
        observations.observed_arrival_time,
        observations.observed_arrival_ts,
        observations.source_system as observed_source_system,
        observations.feed_scope as observed_feed_scope,
        observations.operator_id as observed_operator_id,
        observations.snapshot_label as observed_snapshot_label,
        observations.ingested_at as observed_ingested_at,
        count(*) over (
            partition by
                observations.service_date,
                observations.trip_id,
                observations.stop_id,
                observations.stop_sequence,
                observations.snapshot_label
        ) as observation_key_row_count
    from {{ ref('stg_stop_observations') }} as observations
),
trip_service_candidates as (
    select
        observed.service_date,
        observed.trip_id,
        count(scheduled.trip_id) as scheduled_trip_service_date_count
    from observed_base as observed
    left join {{ ref('scheduled_stop_events') }} as scheduled
      on scheduled.service_date = observed.service_date
     and scheduled.trip_id = observed.trip_id
    group by
        observed.service_date,
        observed.trip_id
),
trip_service_sequence_candidates as (
    select
        observed.service_date,
        observed.trip_id,
        observed.stop_sequence,
        count(scheduled.trip_id) as scheduled_trip_service_sequence_count
    from observed_base as observed
    left join {{ ref('scheduled_stop_events') }} as scheduled
      on scheduled.service_date = observed.service_date
     and scheduled.trip_id = observed.trip_id
     and scheduled.stop_sequence = observed.stop_sequence
    group by
        observed.service_date,
        observed.trip_id,
        observed.stop_sequence
)
select
    observed.service_date,
    observed.trip_id,
    scheduled.route_id,
    scheduled.service_id,
    observed.stop_id as observed_stop_id,
    scheduled.stop_id as scheduled_stop_id,
    observed.stop_sequence,
    scheduled.trip_headsign,
    scheduled.direction_id,
    scheduled.shape_id,
    scheduled.shape_dist_traveled,
    scheduled.arrival_time_text as scheduled_arrival_time_text,
    scheduled.departure_time_text as scheduled_departure_time_text,
    scheduled.arrival_time_secs as scheduled_arrival_time_secs,
    scheduled.departure_time_secs as scheduled_departure_time_secs,
    case
        when scheduled.arrival_time_secs is null then null
        else (
            observed.service_date::timestamp
            + scheduled.arrival_time_secs * interval '1 second'
        ) at time zone 'America/Los_Angeles'
    end as scheduled_arrival_ts,
    case
        when scheduled.departure_time_secs is null then null
        else (
            observed.service_date::timestamp
            + scheduled.departure_time_secs * interval '1 second'
        ) at time zone 'America/Los_Angeles'
    end as scheduled_departure_ts,
    observed.observed_arrival_time,
    observed.observed_arrival_ts,
    case
        when scheduled.arrival_time_secs is null then null
        else extract(
            epoch from (
                observed.observed_arrival_ts
                - (
                    observed.service_date::timestamp
                    + scheduled.arrival_time_secs * interval '1 second'
                ) at time zone 'America/Los_Angeles'
            )
        )::integer
    end as arrival_delay_secs,
    observed.observed_source_system,
    observed.observed_feed_scope,
    observed.observed_operator_id,
    observed.observed_snapshot_label,
    observed.observed_ingested_at,
    scheduled.source_system as scheduled_source_system,
    scheduled.feed_scope as scheduled_feed_scope,
    scheduled.operator_id as scheduled_operator_id,
    scheduled.snapshot_label as scheduled_snapshot_label,
    observed.observation_key_row_count,
    trip_candidates.scheduled_trip_service_date_count,
    sequence_candidates.scheduled_trip_service_sequence_count,
    case
        when observed.observation_key_row_count > 1 then 'duplicate_observation_key'
        when scheduled.trip_id is not null then 'matched_exact'
        when coalesce(trip_candidates.scheduled_trip_service_date_count, 0) = 0 then 'unmatched_trip_service_date'
        when coalesce(sequence_candidates.scheduled_trip_service_sequence_count, 0) = 0 then 'unmatched_stop_sequence'
        else 'unmatched_stop_id'
    end as join_status
from observed_base as observed
left join {{ ref('scheduled_stop_events') }} as scheduled
  on scheduled.service_date = observed.service_date
 and scheduled.trip_id = observed.trip_id
 and scheduled.stop_sequence = observed.stop_sequence
 and scheduled.stop_id = observed.stop_id
left join trip_service_candidates as trip_candidates
  on trip_candidates.service_date = observed.service_date
 and trip_candidates.trip_id = observed.trip_id
left join trip_service_sequence_candidates as sequence_candidates
  on sequence_candidates.service_date = observed.service_date
 and sequence_candidates.trip_id = observed.trip_id
 and sequence_candidates.stop_sequence = observed.stop_sequence
