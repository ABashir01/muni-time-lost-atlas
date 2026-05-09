{{ config(materialized='table', tags=['serving', 'gis']) }}

select
    overlay_id,
    street_name,
    segment_name,
    route_hint,
    geom,
    source_system,
    feed_scope,
    operator_id,
    snapshot_label,
    ingested_at
from {{ ref('stg_transit_only_lanes') }}
