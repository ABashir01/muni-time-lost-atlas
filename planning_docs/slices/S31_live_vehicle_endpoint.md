# Title
S31 Live Vehicle Endpoint

## Goal
Expose a lightweight API endpoint for current live vehicle positions.

## Why this slice exists
The frontend should consume live-vehicle data through the same documented serving boundary as the rest of the product.

## Depends on
- `S30_gtfs_rt_ingest`

## Touches
- live vehicle endpoint
- API contract doc
- endpoint integration tests

## Inputs
- parsed live vehicle state

## Outputs
- `GET /live/vehicles`

## Implementation notes
- define stale-data behavior explicitly
- keep payload map-friendly and small

## Tests required
- happy-path endpoint test
- stale/no-data behavior test

## Acceptance criteria
- live vehicle endpoint is documented and testable

## Non-goals
- map overlay UI
- additional GTFS-RT metrics

## Handoff to next slice
Next slice adds the optional live map overlay.

## Completion notes

