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
