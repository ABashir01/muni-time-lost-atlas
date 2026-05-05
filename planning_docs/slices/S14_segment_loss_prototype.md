# Title
S14 Segment Loss Prototype

## Goal
Define and implement the first narrow segment-level or corridor-level time-loss representation for route detail and map use.

## Why this slice exists
The map and route pages need a place-based explanation of where loss happens, not just route-level totals.

## Depends on
- `S11_metrics_mart_prototype`
- `S12_geometry_ingest`

## Touches
- segment or corridor aggregation logic
- spatial metric models
- methodology/data-model docs if segment identity is clarified

## Inputs
- route geometry
- observed/scheduled runtime data

## Outputs
- first segment-level loss output

## Implementation notes
- keep segment identity simple and documented
- prefer one workable approach over a universal corridor model

## Tests required
- one route fixture proving segment output can be generated
- shape/metric alignment sanity test

## Acceptance criteria
- route detail and map slices have a stable segment-level metric to consume

## Non-goals
- citywide spatial optimization
- lane-impact claims

## Handoff to next slice
Next slice starts the API skeleton.

## Completion notes

