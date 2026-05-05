# Title
S11 Metrics Mart Prototype

## Goal
Materialize the first route-level metrics mart that can support ranked queries for a selected time window.

## Why this slice exists
Later API work should query a stable mart instead of recomputing metrics ad hoc.

## Depends on
- `S10_route_level_metric`

## Touches
- transformation layer
- first route metrics mart
- data model docs if schema is clarified

## Inputs
- route-level metric definitions
- canonical scheduled/observed models

## Outputs
- route metrics mart suitable for ranking endpoints

## Implementation notes
- start with one or two windows only
- keep schema small and API-friendly

## Tests required
- query smoke test returning ranked routes
- checks for expected required fields

## Acceptance criteria
- mart exists and returns stable route-level metrics
- API slices can use it directly

## Non-goals
- segment-level metrics
- map geometry work
- live data

## Handoff to next slice
Next slice ingests and validates route and stop geometries.

## Completion notes

