{{ config(materialized='table', tags=['scheduled']) }}

select
    route_id,
    agency_id,
    route_short_name,
    route_long_name,
    route_type,
    route_color,
    route_text_color,
    source_system,
    feed_scope,
    operator_id,
    snapshot_label
from {{ ref('stg_gtfs_routes') }}
