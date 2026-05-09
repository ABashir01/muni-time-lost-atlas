# Title
B1 Core Metrics Bundle

## Goal
Produce the first usable rider-time-loss metric layer from the joined scheduled/observed data.

## Why this bundle exists
The historical product cannot move into API or frontend work until the core metric contract is real, stable, and queryable from the database.

## Depends on
- `S07_scheduled_observed_join`

## Touches
- SQL-first metric transformations
- metric materialization entrypoints if needed
- route/window marts
- route/hour and route/direction summaries
- methodology-aligned metric naming

## Inputs
- `canonical.scheduled_stop_events`
- `canonical.observed_stop_events`
- `canonical.observed_stop_event_join_audit`
- methodology definitions in `02_methodology.md`

## Outputs
- first route-level rider-time-loss marts
- stable metric field names for API work:
  - `typical_trip_loss_minutes`
  - `waiting_loss_minutes`
  - `in_vehicle_loss_minutes`

## Implementation notes
- use SQL-first transformations in this bundle
- define waiting-time math on the current joined model
- define in-vehicle delay math on the current joined model
- define the route-level “typical trip loss” metric
- materialize at least:
  - route-window summary
  - route-direction summary
  - route-hour summary
- keep the first metric scope narrow and explicit
- clearly separate matched rows from unmatched rows
- do not add fuzzy historic reconciliation
- do not add bunching unless it falls out naturally with very low complexity
- add a Python entrypoint only if it materially improves repeatability

## Tests required
- one primary integration suite proving metric outputs are plausible on controlled inputs
- one regression check only if this bundle materially changes the `S07` join shape

## Acceptance criteria
- route-level metric tables exist and are queryable
- metric outputs use the expected public-facing names
- the tables are sufficient for the historical/static API bundle to read directly

## Non-goals
- dbt scaffolding
- GIS/segment modeling
- API handlers
- frontend work

## Handoff to next bundle
`B2_dbt_adoption_bundle` should migrate the proven SQL graph into dbt without redesigning the metric semantics.

## Completion notes
- what changed
  - added `db/sql/05-materialize-core-metrics.sql` to materialize `marts.route_window_summary`, `marts.route_direction_summary`, and `marts.route_hour_summary`
  - added `pipeline/src/muni_lta_pipeline/core_metrics.py` as the repeatable SQL entrypoint
  - added controlled `metrics_core` GTFS and stop-observations fixtures for B1 integration testing
  - documented the matched-only metric scope, first-stop waiting math, terminal-to-terminal runtime math, and `all_day` window limitation
- what tests were run
  - `.\.venv\Scripts\python.exe -m unittest tests.integration.test_core_metrics_bundle -v`
- what passed
  - controlled route-window, route-direction, and route-hour metrics matched the expected waiting and in-vehicle loss math
  - unmatched observation rows stayed outside the metric numerators and remained visible through join-status and summary counts
- any known limitations or follow-up issues
  - `B1` only materializes the `all_day` route window
  - waiting loss currently depends on consecutive matched first-stop observations only
  - in-vehicle loss currently uses matched first/last observed arrivals because observed departures are not yet available in the canonical joined model
