# Title
S16 Rankings Endpoint

## Goal
Expose route rankings by window and metric from the first stable metrics mart.

## Why this slice exists
The homepage and ranking-first product story depend on a clear rankings contract.

## Depends on
- `S15_api_skeleton`
- `S11_metrics_mart_prototype`

## Touches
- rankings endpoint
- API contract doc
- integration tests

## Inputs
- route metrics mart
- fields in `05_api_contract.md`

## Outputs
- `GET /rankings` endpoint

## Implementation notes
- keep supported params narrow at first
- prefer explicit validation to permissive parsing

## Tests required
- happy-path rankings response
- bad param validation
- response-field assertion

## Acceptance criteria
- rankings endpoint serves a stable schema
- frontend fixture slices can mirror the same contract

## Non-goals
- route detail
- compare
- live vehicles

## Handoff to next slice
Next slice adds the route summary endpoint.

## Completion notes

