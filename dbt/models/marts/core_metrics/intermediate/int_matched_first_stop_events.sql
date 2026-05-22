{{ config(materialized=var('metrics_intermediate_materialization', 'ephemeral'), tags=['metrics']) }}

select
    terminals.route_id,
    terminals.direction_id,
    terminals.trip_headsign,
    terminals.service_date,
    terminals.trip_id,
    terminals.first_stop_id,
    terminals.first_stop_trip_order,
    terminals.first_scheduled_arrival_ts,
    observed_first.observed_arrival_ts as observed_first_arrival_ts
from {{ ref('int_scheduled_trip_terminals') }} as terminals
join {{ ref('observed_stop_events') }} as observed_first
  on observed_first.trip_id = terminals.trip_id
 and observed_first.service_date = terminals.service_date
 and observed_first.stop_sequence = terminals.first_stop_sequence
 and observed_first.stop_id = terminals.first_stop_id
where terminals.first_scheduled_arrival_ts is not null
