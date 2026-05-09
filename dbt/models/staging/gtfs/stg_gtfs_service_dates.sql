{{ config(materialized='table', tags=['scheduled']) }}

with latest_snapshot as (
    {{ latest_active_snapshot_subquery() }}
),
calendar_expanded as (
    select
        calendar.service_id,
        service_day::date as service_date,
        calendar.source_system,
        calendar.feed_scope,
        nullif(calendar.operator_id, '') as operator_id,
        calendar.snapshot_label
    from {{ source('raw', 'gtfs_calendar') }} as calendar
    cross join latest_snapshot
    cross join lateral generate_series(
        to_date(calendar.start_date, 'YYYYMMDD'),
        to_date(calendar.end_date, 'YYYYMMDD'),
        interval '1 day'
    ) as service_day
    where calendar.feed_scope = 'operator_active'
      and calendar.snapshot_label = latest_snapshot.snapshot_label
      and case extract(isodow from service_day)::integer
          when 1 then calendar.monday = '1'
          when 2 then calendar.tuesday = '1'
          when 3 then calendar.wednesday = '1'
          when 4 then calendar.thursday = '1'
          when 5 then calendar.friday = '1'
          when 6 then calendar.saturday = '1'
          when 7 then calendar.sunday = '1'
          else false
      end
),
calendar_date_additions as (
    select
        calendar_dates.service_id,
        to_date(calendar_dates.date, 'YYYYMMDD') as service_date,
        calendar_dates.source_system,
        calendar_dates.feed_scope,
        nullif(calendar_dates.operator_id, '') as operator_id,
        calendar_dates.snapshot_label
    from {{ source('raw', 'gtfs_calendar_dates') }} as calendar_dates
    cross join latest_snapshot
    where calendar_dates.feed_scope = 'operator_active'
      and calendar_dates.snapshot_label = latest_snapshot.snapshot_label
      and calendar_dates.exception_type = '1'
),
calendar_date_removals as (
    select
        calendar_dates.service_id,
        to_date(calendar_dates.date, 'YYYYMMDD') as service_date
    from {{ source('raw', 'gtfs_calendar_dates') }} as calendar_dates
    cross join latest_snapshot
    where calendar_dates.feed_scope = 'operator_active'
      and calendar_dates.snapshot_label = latest_snapshot.snapshot_label
      and calendar_dates.exception_type = '2'
),
combined_service_dates as (
    select * from calendar_expanded
    union
    select * from calendar_date_additions
)
select distinct
    combined.service_id,
    combined.service_date,
    combined.source_system,
    combined.feed_scope,
    combined.operator_id,
    combined.snapshot_label
from combined_service_dates as combined
left join calendar_date_removals as removals
  on combined.service_id = removals.service_id
 and combined.service_date = removals.service_date
where removals.service_id is null
