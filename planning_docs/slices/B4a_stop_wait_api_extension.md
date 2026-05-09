# Title
B4a Stop Wait API Extension

## Goal
Expose stop-based waiting hotspots through a dedicated historical/static API endpoint.

## Why this bundle exists
`B3a` created a real stop-wait serving layer, but `B4` intentionally deferred a standalone stop-wait endpoint. This bundle closes that gap before broader frontend integration.

## Depends on
- `B3a_stop_wait_metrics_bundle`
- `B4_api_bundle`

## Touches
- FastAPI app routes
- Pydantic response models
- API repository queries
- fixture payload generation
- API contract docs

## Inputs
- `serving.stop_wait_hotspots`
- current route-detail API contract
- stop-wait labels already present in route summaries

## Outputs
- `GET /routes/{route_id}/stops/wait`
- fixture payload for stop-wait hotspots
- contract-tested response model

## Implementation notes
- add a read-only endpoint:
  - `GET /routes/{route_id}/stops/wait?window=&direction=`
- use the existing stop-wait serving layer
- keep the response shape explicit about:
  - stop geometry
  - stop wait strategy
  - waiting loss
  - matched headway interval count
- preserve the current conservative scope:
  - first-stop exact-match strategy
  - `all_day` only unless broader windows are already supported

## Tests required
- one primary API integration suite covering the new stop-wait endpoint
- one fixture-contract check ensuring the committed stop-wait payload matches the response model

## Acceptance criteria
- the stop-wait endpoint returns a stable documented shape
- fixture payload exists for route-detail/frontend work
- the API layer remains thin and read-oriented

## Non-goals
- changing the underlying stop-wait methodology
- adding live/realtime data
- redesigning the route summary endpoints

## Handoff to next bundle
`B6_frontend_api_integration_bundle` can use this endpoint for route-detail stop hotspot views without inventing ad hoc fixture-only UI behavior.

## Completion notes
- added `GET /routes/{route_id}/stops/wait?window=all_day&direction=` to the FastAPI surface using a thin repository read over `serving.stop_wait_hotspots`
- added dedicated Pydantic stop-wait FeatureCollection response models and a committed `fixtures/api/route_14_stops_wait_direction_1_all_day.json` payload
- updated `planning_docs/05_api_contract.md` and `api/README.md` to document the new endpoint and fixture
- tests run:
  - `.\.venv\Scripts\python.exe -m unittest tests.integration.test_api_bundle tests.unit.test_api_contract_fixtures`
- passed:
  - API integration coverage for the new stop-wait endpoint
  - fixture contract validation for the committed stop-wait payload
- known limitations:
  - endpoint scope remains `window=all_day` only
  - stop-wait rows remain limited to the existing first-stop exact-match strategy
