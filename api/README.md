# API

FastAPI service for the thin historical/static API surface.

Current package layout:

- `src/muni_lta_api/__init__.py`
  - package marker and version
- `src/muni_lta_api/config.py`
  - environment-driven config bootstrap and local Postgres URL assembly
- `src/muni_lta_api/app.py`
  - application factory and B4 endpoint registration
- `src/muni_lta_api/db.py`
  - small `psycopg` connection wrapper for read queries
- `src/muni_lta_api/models.py`
  - frozen Pydantic response models for the documented API contract
- `src/muni_lta_api/repository.py`
  - targeted SQL reads against the dbt-managed marts and serving tables

Current endpoint surface:
- `GET /health`
- `GET /rankings`
- `GET /routes/{route_id}/summary`
- `GET /routes/{route_id}/segments`
- `GET /routes/{route_id}/stops/wait`
- `GET /routes/compare`
- `GET /map/routes`

Deferred from B4:
- `GET /live/vehicles`
