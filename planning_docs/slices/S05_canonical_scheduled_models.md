# Title
S05 Canonical Scheduled Models

## Goal
Transform raw GTFS static data into stable scheduled entities that downstream metrics can depend on.

## Why this slice exists
Raw GTFS is not a dependable interface for later calculations. Canonical scheduled models reduce source quirks and fix naming/stability.

## Depends on
- `S04_gtfs_static_fixture_ingest`

## Touches
- staging models
- canonical scheduled models
- dbt or transformation layer definitions

## Inputs
- raw GTFS fixture tables
- modeling guidance in `06_data_model.md`

## Outputs
- canonical scheduled route/trip/stop/stop-event models

## Implementation notes
- focus on stable keys and normalized timestamps/service dates
- define the first canonical scheduled stop-event representation

## Tests required
- uniqueness tests
- nullability checks on required keys
- referential checks between canonical entities

## Acceptance criteria
- downstream slices can query scheduled entities without touching raw GTFS directly
- canonical scheduled stop events exist and pass basic tests

## Non-goals
- historical joins
- waiting or runtime metrics
- route-level aggregates

## Handoff to next slice
Next slice ingests historic stop observations into raw tables.

## Completion notes
- Changed files:
  - `db/sql/02-materialize-canonical-scheduled-models.sql`
  - `pipeline/src/muni_lta_pipeline/canonical_scheduled_models.py`
  - `tests/integration/test_canonical_scheduled_models.py`
  - `pipeline/README.md`
  - `tests/README.md`
  - `README.md`
  - `planning_docs/09_decisions.md`
  - `planning_docs/slices/S05_canonical_scheduled_models.md`
- What changed:
  - added a SQL-first scheduled-model materialization file that creates the first `staging` and `canonical` scheduled GTFS tables
  - created typed staging tables for routes, trips, stops, stop_times, shapes, and expanded service dates
  - created the first canonical scheduled tables:
    - `canonical.scheduled_routes`
    - `canonical.scheduled_trips`
    - `canonical.scheduled_stops`
    - `canonical.service_dates`
    - `canonical.scheduled_stop_events`
  - normalized GTFS stop times into `arrival_time_text` / `departure_time_text` plus service-day-relative `arrival_time_secs` / `departure_time_secs`
  - expanded `service_date` values from `calendar.txt` and `calendar_dates.txt`, including fixture removal exceptions
  - added a thin Python entrypoint that runs the scheduled-model SQL after ensuring the local DB is ready
  - added a DB-backed integration test covering counts, uniqueness, nullability, referential integrity, and queryable scheduled stop events
  - recorded the early SQL-first transformation choice in `planning_docs/09_decisions.md`
- Tests run:
  - `& 'C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest tests.integration.test_canonical_scheduled_models -v`
  - `& 'C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests -v`
  - `@' ... import muni_lta_pipeline.canonical_scheduled_models ... '@ | & 'C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -`
- Results:
  - the canonical-model module imports successfully and points at the expected SQL materialization file
  - the targeted DB-backed canonical integration test passes end to end once run from a shell that can reach the local Docker/Postgres service
  - repository `unittest discover` still passes for the existing unit suite
- Follow-up issues:
  - early scheduled models are materialized via SQL files and a Python wrapper for now; the repo still needs a later slice to introduce the actual `dbt` project scaffolding
  - canonical route geometry and canonical observed-stop entities remain later slices
- Revision notes:
  - replaced positional `SELECT *` inserts for canonical tables with explicit column lists
  - fixed the `canonical.scheduled_trips` insert order bug that could place `route_id` values into the `trip_id` primary key slot and trigger foreign-key failures
  - aligned the other canonical inserts to the same explicit-column pattern so later column-order drift does not silently break materialization
