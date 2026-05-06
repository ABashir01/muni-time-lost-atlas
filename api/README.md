# API

Reserved for the separate `FastAPI` service.

Current package layout:

- `src/muni_lta_api/__init__.py`
  - package marker and version
- `src/muni_lta_api/config.py`
  - environment-driven config bootstrap
- `src/muni_lta_api/app.py`
  - lazy `FastAPI` application factory without endpoints yet

Expected future ownership:

- HTTP endpoints for rankings, route detail, compare, and map data
- request and response validation
- thin database access over precomputed marts
- API-focused tests
