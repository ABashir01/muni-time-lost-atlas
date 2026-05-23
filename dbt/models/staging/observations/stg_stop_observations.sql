{{ config(materialized='table', tags=['observed']) }}

with selected_snapshot as (
    {{ target_observed_snapshot_subquery() }}
),
filtered_observations as (
    select observations.*
    from {{ source('raw', 'stop_observations') }} as observations
    cross join selected_snapshot
    where observations.feed_scope = '{{ target_observed_feed_scope() }}'
      and observations.snapshot_label = selected_snapshot.snapshot_label
      and (
          '{{ target_observed_feed_scope() }}' != 'regional_historic'
          or observations.trip_id like '{{ historic_agency_id() }}:%'
      )
)

select
    case
        when feed_scope = 'regional_historic'
         and trip_id ~ '^[^:]+:.+:\d{8}$'
         and to_date(right(trip_id, 8), 'YYYYMMDD') = service_date + 1
        then service_date + 1
        else service_date
    end as service_date,
    trip_id,
    stop_id,
    stop_sequence,
    observed_arrival_time,
    case
        when feed_scope = 'regional_historic'
         and trip_id ~ '^[^:]+:.+:\d{8}$'
         and to_date(right(trip_id, 8), 'YYYYMMDD') = service_date + 1
        then observed_arrival_ts + interval '1 day'
        else observed_arrival_ts
    end as observed_arrival_ts,
    source_system,
    feed_scope,
    nullif(operator_id, '') as operator_id,
    snapshot_label,
    ingested_at
from filtered_observations
