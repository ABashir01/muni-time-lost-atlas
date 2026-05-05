# Title
S19 Compare Endpoint

## Goal
Expose a small compare contract for 2-4 selected routes in one time window.

## Why this slice exists
The compare view is a distinct product surface and should have a dedicated documented response.

## Depends on
- `S16_rankings_endpoint`
- `S17_route_summary_endpoint`

## Touches
- compare endpoint
- API contract doc
- integration tests

## Inputs
- route summary fields
- compare requirements from `01_product_experience.md`

## Outputs
- `GET /routes/compare`

## Implementation notes
- do not invent separate field names if shared ones work
- validate route count and input shape explicitly

## Tests required
- 2-route compare test
- invalid route-count validation test
- response-field assertion

## Acceptance criteria
- compare endpoint supports the intended MVP compare view

## Non-goals
- route page
- live vehicles
- ranking-specific layout concerns

## Handoff to next slice
Next slice bootstraps the Next.js frontend app.

## Completion notes

