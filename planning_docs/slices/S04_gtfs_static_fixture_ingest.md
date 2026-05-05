# Title
S04 GTFS Static Fixture Ingest

## Goal
Load a very small GTFS static fixture into raw tables and prove that core schedule entities can be parsed and stored correctly.

## Why this slice exists
The entire project depends on a reliable scheduled baseline. This slice proves the ingest path before scale or historical joins.

## Depends on
- `S02_database_bootstrap`
- `S03_python_project_bootstrap`

## Touches
- GTFS raw ingest code
- raw table definitions for static GTFS
- fixture input files

## Inputs
- operator-specific Muni GTFS shape assumptions from `03_data_sources.md`

## Outputs
- raw GTFS tables
- successful load of a small fixture covering routes, trips, stops, stop_times, and shapes

## Implementation notes
- use a very small deterministic fixture
- prioritize parse correctness over feed completeness

## Tests required
- row-count assertions for loaded GTFS entities
- basic referential sanity checks between trips, stop_times, and stops

## Acceptance criteria
- core GTFS tables load without manual cleanup
- fixture load is repeatable
- failures are actionable and visible

## Non-goals
- canonical models
- historical observations
- metrics

## Handoff to next slice
Next slice builds canonical scheduled models from the raw GTFS tables.

## Completion notes

