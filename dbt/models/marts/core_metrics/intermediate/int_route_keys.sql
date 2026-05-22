{{ config(materialized=var('metrics_intermediate_materialization', 'ephemeral'), tags=['metrics']) }}

select route_id from {{ ref('int_matched_stop_event_coverage') }}
union
select route_id from {{ ref('int_unmatched_resolved') }}
union
select route_id from {{ ref('int_full_trip_metrics') }}
union
select route_id from {{ ref('int_headway_intervals') }}
