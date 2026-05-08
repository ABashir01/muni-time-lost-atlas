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
- raw GTFS fixture ingest for `S04_gtfs_static_fixture_ingest`
- active `511` GTFS acquisition for `S04a_511_active_gtfs_fetch`
- historic regional `511` GTFS acquisition for `S06a_511_historic_rg_feed_fetch`
- canonical scheduled GTFS models for `S05_canonical_scheduled_models`
- raw historic stop observations fixture ingest for `S06_historic_stop_observations_ingest`
- real historic stop observations archive ingest for `S06b_real_historic_stop_observations_load`

Not included yet:

- framework initialization
- transit business logic
- product implementation

Current transit data artifact:

- a tiny deterministic GTFS static fixture under `fixtures/gtfs_static/minimal`
- a raw ingest loader at `pipeline/src/muni_lta_pipeline/gtfs_static_fixture_ingest.py`
- accepted raw GTFS table DDL at `db/sql/01-create-raw-gtfs-tables.sql`
- an active-feed fetcher at `pipeline/src/muni_lta_pipeline/active_gtfs_fetch.py`
- a historic regional fetcher at `pipeline/src/muni_lta_pipeline/historic_rg_feed_fetch.py`
- scheduled model materialization at `pipeline/src/muni_lta_pipeline/canonical_scheduled_models.py`
- a historic stop-observations fixture loader at `pipeline/src/muni_lta_pipeline/historic_stop_observations_fixture_ingest.py`
- a real historic stop-observations archive loader at `pipeline/src/muni_lta_pipeline/historic_stop_observations_archive_ingest.py`
- gitignored local acquisition artifacts under `artifacts/acquisitions/511/operator_active`

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

## Active 511 GTFS acquisition

The project now has a separate acquisition step for the active operator-specific Muni GTFS feed from `511`.

- set `TRANSIT_511_API_KEY` in the repo-root `.env`
- the fetcher targets `operator_id=SF`
- successful downloads are archived locally as:
  - a timestamped `.zip`
  - a neighboring `.json` provenance/validation record
- default artifact location:
  - `artifacts/acquisitions/511/operator_active/`

Example command with the bundled Python runtime:

```powershell
& 'C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\pipeline\src\muni_lta_pipeline\active_gtfs_fetch.py
```

Optional live verification test:

```powershell
& 'C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest tests.integration.test_511_active_gtfs_fetch -v
```

## Historic 511 regional GTFS acquisition

The project now also has a separate acquisition step for monthly historic `511` regional GTFS feeds used by retrospective analysis.

- set `TRANSIT_511_API_KEY` in the repo-root `.env`
- the fetcher targets `operator_id=RG`
- pass `--historic-month YYYY-MM`
- use `--with-stop-observations` to request the historic `-so` variant with `stop_observations.txt`
- successful downloads are archived locally as:
  - a timestamped `.zip`
  - a neighboring `.json` provenance/validation record
- default artifact location:
  - `artifacts/acquisitions/511/regional_historic/`

Example commands with the bundled Python runtime:

```powershell
& 'C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\pipeline\src\muni_lta_pipeline\historic_rg_feed_fetch.py --historic-month 2023-02
& 'C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\pipeline\src\muni_lta_pipeline\historic_rg_feed_fetch.py --historic-month 2023-02 --with-stop-observations
```

Optional live verification test:

```powershell
& 'C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest tests.integration.test_511_historic_rg_feed_fetch -v
```

## Canonical scheduled models

The project now has a first scheduled-model materialization layer on top of the raw GTFS fixture.

- uses `staging` for typed GTFS normalization
- uses `canonical` for stable scheduled entities
- expands service dates from `calendar.txt` and `calendar_dates.txt`
- keeps service-day-relative times as seconds for downstream calculations

Example command:

```powershell
& 'C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\pipeline\src\muni_lta_pipeline\canonical_scheduled_models.py
```

## Historic stop observations fixture ingest

The project now has a fixture-driven raw ingest path for historical `stop_observations`.

- loads `fixtures/stop_observations/regional_rg_minimal/stop_observations.txt`
- creates and populates `raw.stop_observations`
- preserves source-facing observation fields for `service_date`, `trip_id`, `stop_id`, `stop_sequence`, and `observed_arrival_time`
- derives a typed `observed_arrival_ts` for later scheduled/observed reconciliation work

Example command:

```powershell
& 'C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\pipeline\src\muni_lta_pipeline\historic_stop_observations_fixture_ingest.py
```

## Real historic stop observations archive ingest

The project now also has a real archive-backed raw ingest path for historic `RG` `stop_observations`.

- reads the `.json` sidecar and `.zip` artifact produced by `historic_rg_feed_fetch.py --with-stop-observations`
- loads real archive rows into `raw.stop_observations`
- maps source `to_stop_id` into raw `stop_id`
- parses compact `service_date` values and derives a typed `observed_arrival_ts` from service-day local times
- uses `archive_...` snapshot labels so real loads remain distinguishable from fixture loads

Example command:

```powershell
& 'C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\pipeline\src\muni_lta_pipeline\historic_stop_observations_archive_ingest.py --metadata-path .\artifacts\acquisitions\511\regional_historic\511_regional_historic_RG_202302_with_so_20260508T223557Z.json --max-rows 250
```
