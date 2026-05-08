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
- `integration/test_canonical_scheduled_models.py`
  - loads the GTFS fixture and materializes the first staged/canonical scheduled tables
  - asserts uniqueness and non-null required keys for the canonical scheduled entities
  - asserts referential integrity between canonical trips, stops, service dates, and scheduled stop events
  - verifies the fixture service-calendar exception is applied and scheduled stop events are queryable
- `integration/test_historic_stop_observations_fixture_ingest.py`
  - loads the tiny historic `stop_observations` fixture into `raw.stop_observations`
  - asserts row counts and required non-null observation fields
  - verifies typed timestamp parsing and basic join-key compatibility with the raw GTFS fixture
- `integration/test_511_active_gtfs_fetch.py`
  - performs a live `511` fetch only if `TRANSIT_511_API_KEY` is configured locally
  - skips cleanly when no token is available or network access to `511` is blocked
  - verifies the fetched archive and provenance metadata are usable by later ingest slices
- `integration/test_511_historic_rg_feed_fetch.py`
  - performs a live monthly historic `511` regional fetch only if `TRANSIT_511_API_KEY` is configured locally
  - skips cleanly when no token is available or network access to `511` is blocked
  - verifies the plain historic regional archive and provenance metadata are usable by later historical ingest slices

Current unit artifacts:

- `unit/test_python_bootstrap.py`
  - includes one placeholder unit test
  - verifies the API and pipeline packages can be imported
  - verifies the bootstrap config helpers return the expected settings objects
- `unit/test_511_active_gtfs_fetch.py`
  - verifies the active `511` acquisition URL is built correctly
  - validates GTFS zip structure checks with deterministic in-memory archives
  - verifies a mocked fetch writes both the zip artifact and JSON provenance metadata
- `unit/test_511_historic_rg_feed_fetch.py`
  - verifies the historic `RG` acquisition URL is built correctly for both plain and `-so` variants
  - validates historic zip structure checks, including `stop_observations.txt` expectations
  - verifies mocked historic fetches write both the zip artifact and JSON provenance metadata
- `unit/test_historic_stop_observations_fixture_ingest.py`
  - verifies service-date and observed-arrival timestamp parsing helpers
  - verifies the stop-observations fixture reader preserves required source-facing fields plus typed timestamps

Unit test command:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Bundled-runtime alternative:

```powershell
& 'C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests -v
```
