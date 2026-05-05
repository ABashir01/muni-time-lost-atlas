# Title
S13 Transit Lane Overlay

## Goal
Ingest a transit-only lane overlay and make it available as contextual map geometry.

## Why this slice exists
The product wants to signal GIS fluency and offer route context without making causal claims in MVP.

## Depends on
- `S12_geometry_ingest`

## Touches
- overlay ingest
- spatial tables or models
- data source docs if acquisition details change

## Inputs
- contextual source from `03_data_sources.md`

## Outputs
- transit-only lane geometry layer

## Implementation notes
- treat this as contextual map data only
- no performance-claim logic in this slice

## Tests required
- overlay geometry validity check
- spatial query smoke test

## Acceptance criteria
- overlay exists and can be served later
- product can display the overlay without inventing causal metrics

## Non-goals
- route performance comparison by lane type
- public claims about lane effectiveness

## Handoff to next slice
Next slice defines the first segment-loss prototype.

## Completion notes

