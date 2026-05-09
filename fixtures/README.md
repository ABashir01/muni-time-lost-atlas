# Fixtures

Reserved for small, reviewable fixture datasets used by slices and tests.

Initial subdirectories:

- `gtfs_static/` for small GTFS schedule fixtures
- `stop_observations/` for historical observation fixtures
- `api/` for response fixtures and contract examples
- `geospatial/` for route geometry and overlay fixtures

Fixtures should stay intentionally small so early slices can validate logic without requiring full production data downloads.

Current `B3` geospatial fixture:
- `geospatial/transit_only_lanes/minimal.geojson`
  - two small transit-lane line features aligned to the controlled route fixture
  - intended only to prove contextual overlay loading and spatial queryability

Current `B4` API fixtures:
- `api/health.json`
- `api/rankings_all_day_typical_trip_loss_minutes_routes.json`
- `api/route_14_summary_all_day.json`
- `api/route_14_segments_direction_1_all_day.json`
- `api/routes_compare_14_49_all_day.json`
- `api/map_routes_all_day_typical_trip_loss_minutes.json`

Current `B4` integration data fixture:
- `gtfs_static/api_bundle/`
  - two-route GTFS fixture used to cover rankings, compare, route detail, and map endpoints in one API suite
- `stop_observations/regional_rg_api_bundle/`
  - matching observed-arrival fixture for the same two-route API test scenario
