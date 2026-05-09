{{ config(materialized='table', tags=['scheduled']) }}

select
    service_id,
    service_date,
    source_system,
    feed_scope,
    operator_id,
    snapshot_label
from {{ ref('stg_gtfs_service_dates') }}
