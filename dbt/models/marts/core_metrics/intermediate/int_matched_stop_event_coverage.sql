{{ config(materialized=var('metrics_intermediate_materialization', 'ephemeral'), tags=['metrics']) }}

select
    route_id,
    direction_id,
    service_date,
    extract(hour from scheduled_arrival_ts at time zone 'America/Los_Angeles')::integer
        as hour_local
from {{ ref('observed_stop_events') }}
