{{ config(materialized='ephemeral', tags=['metrics']) }}

select
    route_id,
    direction_id,
    min(trip_headsign) as direction_label
from {{ ref('scheduled_trips') }}
group by route_id, direction_id
