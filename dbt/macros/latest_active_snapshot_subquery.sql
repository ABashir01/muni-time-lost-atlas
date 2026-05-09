{% macro latest_active_snapshot_subquery() -%}
select snapshot_label
from {{ source('raw', 'gtfs_routes') }}
where feed_scope = 'operator_active'
order by ingested_at desc
limit 1
{%- endmacro %}
