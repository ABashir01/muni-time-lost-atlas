{{ config(materialized=var('metrics_intermediate_materialization', 'ephemeral'), tags=['metrics']) }}

select route_id, direction_id, hour_local from {{ ref('int_matched_stop_event_coverage') }}
union
select route_id, direction_id, hour_local from {{ ref('int_unmatched_resolved') }}
union
select route_id, direction_id, trip_start_hour_local as hour_local from {{ ref('int_full_trip_metrics') }}
union
select route_id, direction_id, hour_local from {{ ref('int_headway_intervals') }}
