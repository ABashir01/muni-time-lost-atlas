{{ config(materialized='table', tags=['scheduled']) }}

select
    stop_id,
    stop_name,
    stop_lat,
    stop_lon,
    source_system,
    feed_scope,
    operator_id,
    snapshot_label
from {{ ref('stg_gtfs_stops') }}
