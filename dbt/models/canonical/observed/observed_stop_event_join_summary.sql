{{ config(materialized='view', tags=['observed']) }}

select
    observed_snapshot_label,
    join_status,
    count(*) as row_count
from {{ ref('observed_stop_event_join_audit') }}
group by observed_snapshot_label, join_status
