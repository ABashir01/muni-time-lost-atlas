{{ config(
    materialized=var('observed_join_audit_materialization', 'view'),
    tags=['observed'],
    post_hook=(
        [
            "create index if not exists observed_stop_event_join_audit_status_idx on {{ this }} (join_status)",
            "create index if not exists observed_stop_event_join_audit_trip_stop_idx on {{ this }} (service_date, trip_id, stop_sequence, observed_stop_id)"
        ] if var('observed_join_audit_materialization', 'view') == 'table' and var('performance_indexing', false) else []
    )
) }}

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
),
joined_rows as (
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
        observed.observed_arrival_ts as observed_arrival_ts_raw,
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
        sequence_candidates.scheduled_trip_service_sequence_count
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
),
normalized_rows as (
    select
        joined_rows.*,
        case
            when joined_rows.scheduled_arrival_ts is null then joined_rows.observed_arrival_ts_raw
            when abs(
                extract(
                    epoch from (joined_rows.observed_arrival_ts_raw - joined_rows.scheduled_arrival_ts)
                )
            ) <= abs(
                extract(
                    epoch from ((joined_rows.observed_arrival_ts_raw + interval '1 day') - joined_rows.scheduled_arrival_ts)
                )
            )
             and abs(
                extract(
                    epoch from (joined_rows.observed_arrival_ts_raw - joined_rows.scheduled_arrival_ts)
                )
            ) <= abs(
                extract(
                    epoch from ((joined_rows.observed_arrival_ts_raw - interval '1 day') - joined_rows.scheduled_arrival_ts)
                )
            )
            then joined_rows.observed_arrival_ts_raw
            when abs(
                extract(
                    epoch from ((joined_rows.observed_arrival_ts_raw + interval '1 day') - joined_rows.scheduled_arrival_ts)
                )
            ) <= abs(
                extract(
                    epoch from ((joined_rows.observed_arrival_ts_raw - interval '1 day') - joined_rows.scheduled_arrival_ts)
                )
            )
            then joined_rows.observed_arrival_ts_raw + interval '1 day'
            else joined_rows.observed_arrival_ts_raw - interval '1 day'
        end as observed_arrival_ts
    from joined_rows
)
select
    normalized_rows.service_date,
    normalized_rows.trip_id,
    normalized_rows.route_id,
    normalized_rows.service_id,
    normalized_rows.observed_stop_id,
    normalized_rows.scheduled_stop_id,
    normalized_rows.stop_sequence,
    normalized_rows.trip_headsign,
    normalized_rows.direction_id,
    normalized_rows.shape_id,
    normalized_rows.shape_dist_traveled,
    normalized_rows.scheduled_arrival_time_text,
    normalized_rows.scheduled_departure_time_text,
    normalized_rows.scheduled_arrival_time_secs,
    normalized_rows.scheduled_departure_time_secs,
    normalized_rows.scheduled_arrival_ts,
    normalized_rows.scheduled_departure_ts,
    normalized_rows.observed_arrival_time,
    normalized_rows.observed_arrival_ts,
    case
        when normalized_rows.scheduled_arrival_ts is null then null
        else extract(
            epoch from (
                normalized_rows.observed_arrival_ts
                - normalized_rows.scheduled_arrival_ts
            )
        )::integer
    end as arrival_delay_secs,
    normalized_rows.observed_source_system,
    normalized_rows.observed_feed_scope,
    normalized_rows.observed_operator_id,
    normalized_rows.observed_snapshot_label,
    normalized_rows.observed_ingested_at,
    normalized_rows.scheduled_source_system,
    normalized_rows.scheduled_feed_scope,
    normalized_rows.scheduled_operator_id,
    normalized_rows.scheduled_snapshot_label,
    normalized_rows.observation_key_row_count,
    normalized_rows.scheduled_trip_service_date_count,
    normalized_rows.scheduled_trip_service_sequence_count,
    case
        when normalized_rows.observation_key_row_count > 1 then 'duplicate_observation_key'
        when normalized_rows.route_id is not null then 'matched_exact'
        when coalesce(normalized_rows.scheduled_trip_service_date_count, 0) = 0 then 'unmatched_trip_service_date'
        when coalesce(normalized_rows.scheduled_trip_service_sequence_count, 0) = 0 then 'unmatched_stop_sequence'
        else 'unmatched_stop_id'
    end as join_status
from normalized_rows
