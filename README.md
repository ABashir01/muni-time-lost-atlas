# Muni Lost Time Atlas

This repository is organized to support small, testable implementation slices for the `Muni Lost Time Atlas` MVP.

## Top-level layout

- `frontend/`
  - home for the `Next.js + TypeScript` application
- `api/`
  - home for the separate `FastAPI` service
- `pipeline/`
  - home for ingestion, transformations, and shared data-platform code
- `tests/`
  - home for repository-level automated tests
- `fixtures/`
  - home for small GTFS, observations, API, and geospatial fixture data
- `planning_docs/`
  - source-of-truth planning, methodology, and slice docs

## Slice-first workflow

Start each implementation slice by reading:

1. `planning_docs/00_project_brief.md`
2. `planning_docs/01_product_experience.md`
3. `planning_docs/02_methodology.md`
4. the assigned slice doc in `planning_docs/slices/`

Read additional contract docs as needed:

- `planning_docs/05_api_contract.md` for API work
- `planning_docs/06_data_model.md` for data/platform work
- `planning_docs/09_decisions.md` for prior decisions

## Current status

This repository currently contains:
- the initial project structure from `S01_repo_structure`
- local Postgres/PostGIS bootstrap for `S02_database_bootstrap`
- Python package and test bootstrap for `S03_python_project_bootstrap`

Not included yet:

- framework initialization
- transit schemas or ingest logic
- transit business logic
- product implementation

## Python bootstrap

The repository now includes:
- a root `pyproject.toml` for Python dependency metadata
- `api/src/muni_lta_api` for the future `FastAPI` service package
- `pipeline/src/muni_lta_pipeline` for future ingest and transform code
- repository-level unit tests under `tests/unit`
- a local `.venv` bootstrap path for future Python-package work

The API bootstrap uses a lazy `FastAPI` import so the package structure and tests can exist before all runtime dependencies are installed in every environment.

To create a local virtual environment with a Python 3.12+ interpreter:

```powershell
python -m venv .venv
```

To run the unit test harness from the venv:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Local database bootstrap

The MVP uses a local Docker Compose service for development database work.

- create a local `.env` first:
  - `Copy-Item .env.example .env`
  - open `.env` and set a local-only `POSTGRES_PASSWORD`
  - if your local DB was already initialized with the old inline password, run `docker compose down -v` once so Postgres reinitializes with the `.env` values
- service: `db`
- image: `postgis/postgis:16-3.4`
- database/user/password come from local `.env`

Common commands:

```powershell
docker compose up -d db
docker compose ps
docker compose down
```

Repeatable smoke test:

```powershell
powershell -ExecutionPolicy Bypass -File .\tests\integration\db_smoke_test.ps1
```

The smoke test expects a local `.env`, starts the DB if needed, confirms the `db` service is running, and retries one simple `psql` query until it returns the database name, user, and `PostGIS` version.
