# Title
B6 Frontend API Integration Bundle

## Goal
Connect the reviewed frontend to the live historical/static API.

## Why this bundle exists
The integration step should happen after both the API and the UI are already stable on their own.

## Depends on
- `B4_api_bundle`
- `B5_frontend_static_bundle`

## Touches
- frontend data-loading paths
- request/response validation at integration edges
- loading/error/empty states

## Inputs
- stable historical/static API endpoints
- static frontend screens already validated against fixtures

## Outputs
- complete historical/static end-to-end MVP

## Implementation notes
- replace homepage fixtures with `/rankings`
- replace route detail fixtures with `/routes/{route_id}/summary`
- replace compare fixtures with `/routes/compare`
- replace map fixtures with `/map/routes` and `/routes/{route_id}/segments`
- implement loading, error, and empty states across the product
- keep response validation explicit at the integration edge
- if an API shape changes, update `05_api_contract.md` in the same bundle
- do not add realtime in this bundle

## Tests required
- one primary end-to-end or integration suite covering the historical/static user path
- one regression check for API response consumption in the frontend

## Acceptance criteria
- all major screens are powered by the live historical/static API
- loading/error/empty states are handled cleanly
- the historical/static MVP works end to end without fixtures

## Non-goals
- realtime data
- major design changes

## Handoff to next bundle
`B7_realtime_bundle` should layer live vehicles on top of the already-working historical/static product.

## Completion notes
