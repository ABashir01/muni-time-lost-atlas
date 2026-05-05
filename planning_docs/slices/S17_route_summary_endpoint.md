# Title
S17 Route Summary Endpoint

## Goal
Expose route-level summary data for one route and one time window.

## Why this slice exists
The route detail page needs a stable summary contract before frontend build-out.

## Depends on
- `S16_rankings_endpoint`
- `S14_segment_loss_prototype`

## Touches
- route summary endpoint
- API contract doc
- integration tests

## Inputs
- route metrics
- worst-segment information

## Outputs
- `GET /routes/{route_id}/summary`

## Implementation notes
- keep the response aligned with the shared fields in `05_api_contract.md`
- do not overfit to frontend layout specifics

## Tests required
- happy-path route summary test
- invalid route handling test
- response-field assertion

## Acceptance criteria
- route summary response is documented and stable
- route detail UI can be built against it

## Non-goals
- segment geometry payloads
- compare endpoint
- live vehicles

## Handoff to next slice
Next slice adds map-oriented endpoints.

## Completion notes

