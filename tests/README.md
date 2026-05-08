# Tests

Reserved for repository-level automated tests.

Initial subdirectories:

- `unit/` for narrow logic tests
- `integration/` for database, API, and cross-layer tests

Slice docs should continue to define exactly which tests are required before a change is considered complete.

Current integration artifacts:

- `integration/db_smoke_test.ps1`
  - expects a local `.env` file at the repo root
  - starts the local Docker Compose DB service if needed
  - confirms the `db` service is running
  - retries one simple `psql` query until it succeeds
  - proves the query can read `current_database()`, `current_user`, and `PostGIS_Version()`
- `integration/test_gtfs_static_fixture_ingest.py`
  - loads the tiny GTFS static fixture into the accepted `raw.gtfs_*` tables
  - asserts row counts for routes, trips, stops, stop_times, shapes, calendar, and calendar_dates
  - asserts referential sanity between trips, stop_times, and stops

Current unit artifacts:

- `unit/test_python_bootstrap.py`
  - includes one placeholder unit test
  - verifies the API and pipeline packages can be imported
  - verifies the bootstrap config helpers return the expected settings objects

Unit test command:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Bundled-runtime alternative:

```powershell
& 'C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests -v
```
