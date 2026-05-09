# Title
B4 API Bundle

## Goal
Build the full historical/static FastAPI surface in one coherent pass.

## Why this bundle exists
Once metrics and GIS outputs are stable, the API should be implemented as a thin read layer instead of spreading endpoint work across many tiny slices.

## Depends on
- `B2_dbt_adoption_bundle`
- `B3_gis_segment_metrics_bundle`

## Touches
- FastAPI app shell
- API response models
- endpoint queries
- fixture payload generation
- API contract docs

## Inputs
- stable route-level marts
- stable segment/GIS outputs
- `05_api_contract.md`

## Outputs
- complete historical/static MVP API surface
- fixture payloads for frontend work

## Implementation notes
- implement:
  - `GET /health`
  - `GET /rankings`
  - `GET /routes/{route_id}/summary`
  - `GET /routes/{route_id}/segments`
  - `GET /routes/compare`
  - `GET /map/routes`
- use Pydantic response models
- prefer targeted SQL access over a heavy ORM domain model
- serve only precomputed tables/views from Postgres
- freeze the response models in code and docs together
- do not add live vehicle endpoints in this bundle

## Tests required
- one primary API integration suite covering the historical/static endpoints
- one contract check ensuring fixture payloads match documented response shapes

## Acceptance criteria
- all historical/static endpoints return stable documented shapes
- fixture payloads exist for every frontend surface
- the API layer remains thin and read-oriented

## Non-goals
- realtime endpoints
- frontend rendering

## Handoff to next bundle
`B5_frontend_static_bundle` should build all screens against the fixture payloads from this bundle.

## Completion notes
