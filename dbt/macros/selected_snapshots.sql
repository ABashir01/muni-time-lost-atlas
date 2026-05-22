{% macro target_gtfs_feed_scope() -%}
{{ var('gtfs_feed_scope', 'operator_active') }}
{%- endmacro %}

{% macro target_gtfs_snapshot_subquery() -%}
{% set snapshot_label = var('gtfs_snapshot_label', none) %}
{% if snapshot_label %}
select '{{ snapshot_label | replace("'", "''") }}' as snapshot_label
{% else %}
select snapshot_label
from {{ source('raw', 'gtfs_routes') }}
where feed_scope = '{{ target_gtfs_feed_scope() }}'
order by ingested_at desc, snapshot_label desc
limit 1
{% endif %}
{%- endmacro %}

{% macro latest_active_snapshot_subquery() -%}
{{ target_gtfs_snapshot_subquery() }}
{%- endmacro %}

{% macro target_observed_feed_scope() -%}
{{ var('observed_feed_scope', 'regional_historic') }}
{%- endmacro %}

{% macro target_observed_snapshot_subquery() -%}
{% set snapshot_label = var('observed_snapshot_label', none) %}
{% if snapshot_label %}
select '{{ snapshot_label | replace("'", "''") }}' as snapshot_label
{% else %}
select snapshot_label
from {{ source('raw', 'stop_observations') }}
where feed_scope = '{{ target_observed_feed_scope() }}'
order by ingested_at desc, snapshot_label desc
limit 1
{% endif %}
{%- endmacro %}

{% macro historic_agency_id() -%}
{{ var('historic_agency_id', 'SF') }}
{%- endmacro %}
