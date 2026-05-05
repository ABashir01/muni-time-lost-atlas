# Title
S30 GTFS-RT Ingest

## Goal
Fetch and parse live GTFS-RT vehicle positions from 511 and persist a current snapshot path.

## Why this slice exists
Live vehicles are useful context, but they are intentionally deferred until the historical/static MVP is correct.

## Depends on
- `S15_api_skeleton`
- historical/static correctness through `S29_compare_integration`

## Touches
- GTFS-RT ingest code
- raw or serving-layer live vehicle storage
- data source notes if needed

## Inputs
- 511 GTFS-RT feed

## Outputs
- repeatable live vehicle ingest path

## Implementation notes
- keep polling modest
- prioritize freshness visibility and simple persistence

## Tests required
- parser test using a GTFS-RT fixture if available
- freshness/staleness smoke test

## Acceptance criteria
- live vehicle positions can be fetched and represented reliably

## Non-goals
- frontend overlay
- trip-update analytics

## Handoff to next slice
Next slice exposes the live vehicle endpoint.

## Completion notes

