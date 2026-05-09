# Title
B4 API Bundle

## Goal
Build the full historical/static FastAPI surface in one coherent pass.

## Why this bundle exists
Once metrics and GIS outputs are stable, the API should be implemented as a thin read layer instead of spreading endpoint work across many tiny slices.

## Depends on
- `B2_dbt_adoption_bundle`
- `B3_gis_segment_metrics_bundle`
- `B3a_stop_wait_metrics_bundle`

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
- include stop-based waiting hotspot outputs if `B3a` lands them in a stable serving layer
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
- Added the full historical/static FastAPI read surface for `GET /health`, `GET /rankings`, `GET /routes/{route_id}/summary`, `GET /routes/{route_id}/segments`, `GET /routes/compare`, and `GET /map/routes`.
- Kept the API thin by querying only the existing `marts.*` and `serving.*` relations with targeted SQL through `psycopg`, including route-hour lookups for `worst_time_band`.
- Froze the public payloads in Pydantic response models and committed matching frontend fixture payloads under `fixtures/api/`.
- Added a dedicated two-route API bundle fixture so rankings, compare, map, and route-detail responses can be exercised together without changing the earlier single-route metric fixture.
- Added `tests/integration/test_api_bundle.py` as the primary historical/static API integration suite and `tests/unit/test_api_contract_fixtures.py` as the fixture contract check.
- Updated the API contract doc to reflect the exact supported params and payload shapes, including the current `all_day`/`routes` scope and the deferred stop-wait and live-vehicle endpoints.
