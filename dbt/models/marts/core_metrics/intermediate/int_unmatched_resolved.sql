{{ config(materialized=var('metrics_intermediate_materialization', 'ephemeral'), tags=['metrics']) }}

select
    coalesce(audit.route_id, scheduled_trip.route_id) as route_id,
    coalesce(audit.direction_id, scheduled_trip.direction_id) as direction_id,
    audit.service_date,
    extract(hour from audit.observed_arrival_ts at time zone 'America/Los_Angeles')::integer
        as hour_local,
    audit.join_status
from {{ ref('observed_stop_event_join_audit') }} as audit
left join {{ ref('scheduled_trips') }} as scheduled_trip
  on scheduled_trip.trip_id = audit.trip_id
where audit.join_status <> 'matched_exact'
  and coalesce(audit.route_id, scheduled_trip.route_id) is not null
