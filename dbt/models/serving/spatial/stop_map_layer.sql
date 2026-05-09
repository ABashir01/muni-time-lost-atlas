{{ config(materialized='table', tags=['serving', 'gis']) }}

select
    stop_id,
    stop_name,
    stop_lat,
    stop_lon,
    geom
from {{ ref('stop_points') }}
