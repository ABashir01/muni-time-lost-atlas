# Title
S02 Database Bootstrap

## Goal
Stand up a local Postgres database with PostGIS enabled and confirm connectivity from the project environment.

## Why this slice exists
All scheduled, observed, and spatial data depend on a working relational + spatial database.

## Depends on
- `S01_repo_structure`

## Touches
- database bootstrap config
- local run instructions
- connectivity smoke tests

## Inputs
- architecture decisions in `04_architecture.md`

## Outputs
- local database bootstrap path
- PostGIS-enabled DB
- one connectivity test or health check

## Implementation notes
- keep this slice to infrastructure bootstrap only
- no GTFS schema work yet

## Tests required
- confirm DB starts locally
- confirm PostGIS extension is available
- confirm one project connection succeeds

## Acceptance criteria
- local Postgres/PostGIS is reachable
- extension is enabled
- the project has one repeatable DB smoke test

## Non-goals
- migrations for transit tables
- ingest logic
- API integration

## Handoff to next slice
Next slice bootstraps the Python project that will connect to this DB.

## Completion notes

- What changed:
  - added root `docker-compose.yml` for a local `Postgres + PostGIS` service using `postgis/postgis:16-3.4`
  - added `db/init/01-enable-postgis.sql` to enable `postgis` and `postgis_topology` on first initialization
  - simplified `tests/integration/db_smoke_test.ps1` into a minimal Windows-friendly smoke test
  - moved local Postgres settings out of inline compose secrets and into a repo-root `.env` flow with `.env.example`
  - updated root `README.md` and `tests/README.md` with local DB bootstrap and smoke-test instructions
  - recorded the bootstrap choice in `planning_docs/09_decisions.md`
- Tests run:
  - `powershell -ExecutionPolicy Bypass -File .\tests\integration\db_smoke_test.ps1`
- Results:
  - the revised smoke test now uses one retrying `psql` query to prove service availability, database connectivity, and `PostGIS` availability in a single pass
  - verification still depends on a local Docker Desktop engine being up and the `db` service being startable through `docker compose`
- Follow-up issues:
  - if Docker Desktop is not running, the smoke test will fail immediately at `docker compose up -d db`
  - if the database was initialized before `db/init/01-enable-postgis.sql` existed, reset the local volume before expecting `PostGIS_Version()` to succeed
  - if the database was initialized before the repo moved to `.env`-driven credentials, reset the local volume once so the new local password takes effect
  - `S03_python_project_bootstrap` should add project-side DB config loading so application code can connect without duplicating connection settings
