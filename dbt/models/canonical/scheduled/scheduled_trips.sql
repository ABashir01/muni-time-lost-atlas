{{ config(materialized='table', tags=['scheduled']) }}

select
    trip_id,
    route_id,
    service_id,
    trip_headsign,
    direction_id,
    shape_id,
    source_system,
    feed_scope,
    operator_id,
    snapshot_label
from {{ ref('stg_gtfs_trips') }}
