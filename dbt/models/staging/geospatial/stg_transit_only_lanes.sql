{{ config(materialized='table', tags=['gis']) }}

with latest_snapshot as (
    select snapshot_label
    from {{ source('raw', 'transit_only_lanes') }}
    order by ingested_at desc, snapshot_label desc
    limit 1
)
select
    overlay_id,
    street_name,
    segment_name,
    nullif(route_hint, '') as route_hint,
    st_setsrid(st_geomfromgeojson(geom_geojson), 4326)::geometry(LineString, 4326) as geom,
    source_system,
    feed_scope,
    nullif(operator_id, '') as operator_id,
    snapshot_label,
    ingested_at
from {{ source('raw', 'transit_only_lanes') }}
where snapshot_label = (select snapshot_label from latest_snapshot)
