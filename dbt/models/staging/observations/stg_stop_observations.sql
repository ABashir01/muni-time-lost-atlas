{{ config(materialized='table', tags=['observed']) }}

select
    service_date,
    trip_id,
    stop_id,
    stop_sequence,
    observed_arrival_time,
    observed_arrival_ts,
    source_system,
    feed_scope,
    nullif(operator_id, '') as operator_id,
    snapshot_label,
    ingested_at
from {{ source('raw', 'stop_observations') }}
