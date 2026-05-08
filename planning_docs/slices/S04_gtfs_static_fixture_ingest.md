# Title
S04 GTFS Static Fixture Ingest

## Goal
Load a very small GTFS static fixture into raw tables and prove that core schedule entities can be parsed and stored correctly.

## Why this slice exists
The entire project depends on a reliable scheduled baseline. This slice proves the ingest path before scale or historical joins.

This is a fixture-proof slice only. It does not prove real 511 acquisition by itself.

## Depends on
- `S02_database_bootstrap`
- `S03_python_project_bootstrap`

## Touches
- GTFS raw ingest code
- raw table definitions for static GTFS
- fixture input files

## Inputs
- operator-specific Muni GTFS shape assumptions from `03_data_sources.md`

## Outputs
- raw GTFS tables
- successful load of a small fixture covering routes, trips, stops, stop_times, and shapes

## Implementation notes
- use a very small deterministic fixture
- prioritize parse correctness over feed completeness

## Tests required
- row-count assertions for loaded GTFS entities
- basic referential sanity checks between trips, stop_times, and stops

## Acceptance criteria
- core GTFS tables load without manual cleanup
- fixture load is repeatable
- failures are actionable and visible

## Non-goals
- canonical models
- historical observations
- metrics
- real 511 feed download

## Handoff to next slice
The next fetch slice proves real active 511 GTFS acquisition; canonical modeling follows after that.

## Completion notes
- Changed files:
  - `db/sql/01-create-raw-gtfs-tables.sql`
  - `fixtures/gtfs_static/minimal/routes.txt`
  - `fixtures/gtfs_static/minimal/trips.txt`
  - `fixtures/gtfs_static/minimal/stops.txt`
  - `fixtures/gtfs_static/minimal/stop_times.txt`
  - `fixtures/gtfs_static/minimal/shapes.txt`
  - `fixtures/gtfs_static/minimal/calendar.txt`
  - `fixtures/gtfs_static/minimal/calendar_dates.txt`
  - `pipeline/src/muni_lta_pipeline/gtfs_static_fixture_ingest.py`
  - `pipeline/README.md`
  - `tests/integration/test_gtfs_static_fixture_ingest.py`
  - `tests/README.md`
  - `README.md`
- What changed:
  - added the accepted `raw.gtfs_*` table DDL in a dedicated SQL file under `db/sql/`
  - added a tiny deterministic GTFS static fixture that exercises routes, trips, stops, stop_times, shapes, calendar, and calendar_dates
  - implemented a slice-scoped Python ingest script that:
    - starts the local Docker Compose `db` service
    - waits for Postgres readiness
    - creates the `raw` schema and GTFS raw tables
    - truncates the GTFS raw tables for repeatable fixture loads
    - parses the fixture CSV files and inserts them into `raw.gtfs_*` with ingest metadata
  - added an integration test that asserts:
    - row counts for each raw GTFS table
    - referential sanity from `stop_times -> trips`, `stop_times -> stops`, and `trips -> routes`
    - the raw `gtfs_stop_times` table preserves source GTFS column names such as `arrival_time` and `departure_time`
  - updated repo docs to describe the new fixture and ingest entrypoint
- Chosen raw ingest approach:
  - keep the fixture tiny and deterministic under `fixtures/gtfs_static/minimal`
  - keep raw typing minimal by storing GTFS source values as `TEXT` plus shared ingest metadata
  - use a Python loader that shells out to local `docker compose exec ... psql` rather than introducing a DB client dependency in `S04`
  - keep the raw GTFS tables as close to source shape as possible, with no source-column renaming during the raw load
- Tests run:
  - `C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -c "from pathlib import Path; import sys; root = Path.cwd(); sys.path.insert(0, str(root / 'pipeline' / 'src')); from muni_lta_pipeline.gtfs_static_fixture_ingest import RAW_GTFS_TABLES, DEFAULT_FIXTURE_DIR; print(len(RAW_GTFS_TABLES)); print(DEFAULT_FIXTURE_DIR.exists())"`
  - `C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest tests.unit.test_python_bootstrap -v`
  - `C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest tests.integration.test_gtfs_static_fixture_ingest -v`
- Results:
  - import / fixture smoke passed and confirmed all 7 raw GTFS table configs plus the fixture directory are present
  - existing unit bootstrap tests passed
  - the DB-backed integration test passed once Docker Desktop was running and the test was rerun with elevated Docker access
- Follow-up issues:
  - Docker-backed integration tests on this machine currently require elevated shell access to talk to the local Docker engine
