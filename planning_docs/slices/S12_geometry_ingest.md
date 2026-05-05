# Title
S12 Geometry Ingest

## Goal
Load route shapes and stop geometries into PostGIS and prove they are spatially valid and queryable.

## Why this slice exists
The frontend map and segment-level analysis need real spatial entities before map endpoints can be designed.

## Depends on
- `S05_canonical_scheduled_models`
- `S11_metrics_mart_prototype`

## Touches
- geometry ingest logic
- spatial tables or models
- spatial validation tests

## Inputs
- GTFS shapes and stops
- modeling guidance from `06_data_model.md`

## Outputs
- route line geometry
- stop point geometry

## Implementation notes
- keep geometry canonical and minimal
- validate SRID and geometry validity explicitly

## Tests required
- geometry validity checks
- sample spatial query smoke test

## Acceptance criteria
- route and stop geometry are stored and queryable
- map slices can rely on spatial data existing

## Non-goals
- transit-lane overlay
- segment metrics
- frontend map

## Handoff to next slice
Next slice adds the transit-only lane overlay as contextual geometry.

## Completion notes

