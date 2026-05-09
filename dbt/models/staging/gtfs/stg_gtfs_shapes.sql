{{ config(materialized='table', tags=['scheduled']) }}

select
    shape_id,
    nullif(shape_pt_lat, '')::double precision as shape_pt_lat,
    nullif(shape_pt_lon, '')::double precision as shape_pt_lon,
    nullif(shape_pt_sequence, '')::integer as shape_pt_sequence,
    nullif(shape_dist_traveled, '')::double precision as shape_dist_traveled,
    source_system,
    feed_scope,
    nullif(operator_id, '') as operator_id,
    snapshot_label
from {{ source('raw', 'gtfs_shapes') }}
where feed_scope = 'operator_active'
  and snapshot_label = ({{ latest_active_snapshot_subquery() }})
