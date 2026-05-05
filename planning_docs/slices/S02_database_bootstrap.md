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
  - added `tests/integration/db_smoke_test.ps1` as a repeatable readiness and connectivity smoke test
  - updated root `README.md` and `tests/README.md` with local DB bootstrap and smoke-test instructions
  - recorded the bootstrap choice in `planning_docs/09_decisions.md`
- Tests run:
  - `powershell -ExecutionPolicy Bypass -File .\tests\integration\db_smoke_test.ps1`
- Results:
  - pending local execution in an environment with Docker available
- Follow-up issues:
  - `S03_python_project_bootstrap` should add project-side DB config loading so application code can connect without duplicating connection settings
