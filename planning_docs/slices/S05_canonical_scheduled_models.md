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

