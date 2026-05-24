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
- `integration/test_historic_stop_observations_archive_ingest.py`
  - performs a live historic `511` `RG` `-so` fetch only if `TRANSIT_511_API_KEY` is configured locally
  - loads a bounded set of real archive observations into `raw.stop_observations`
  - verifies required observation fields, typed timestamps, and snapshot labels distinguish fixture rows from archive-backed rows
- `integration/test_scheduled_observed_join.py`
  - materializes `canonical.observed_stop_events` after the scheduled and observed fixture loads
  - verifies the happy-path fixture rows join exactly and expose both scheduled and observed timestamps
  - verifies unmatched rows are surfaced through explicit join-status counts instead of silently entering the canonical observed model
  - includes an optional live archive-backed join check to confirm real `RG` observation rows remain visibly unmatched until historic schedule reconciliation exists
- `integration/test_core_metrics_bundle.py`
  - loads a controlled multi-trip GTFS + stop-observations fixture for the first `B1` metric layer
  - runs the dbt staged/canonical/mart graph through the existing Python entrypoints and verifies route-window, route-direction, and route-hour summaries
  - confirms waiting loss, in-vehicle loss, and typical trip loss use the expected public field names
  - confirms unmatched observation rows stay outside the metric numerators while remaining visible through separate counts
  - acts as the `B2` dbt-adoption regression check for the API-facing summary tables
- `integration/test_gis_segment_metrics_bundle.py`
  - loads the controlled GTFS + stop-observations fixture plus a tiny transit-lane overlay fixture
  - runs the dbt GIS/segment graph and verifies route geometry, adjacent-stop segment metrics, stop points, and overlay layers are spatially queryable together
  - verifies `worst_segment_label` is populated without changing the accepted core route metric math
- `integration/test_api_bundle.py`
  - loads a dedicated two-route GTFS + stop-observations fixture plus the tiny transit-lane overlay fixture
  - runs the dbt staged/canonical/mart/serving graph and exercises the full historical/static FastAPI surface
  - verifies rankings, route summary, route segments, compare, and map payloads plus narrow validation/error behavior
- `integration/test_511_active_gtfs_fetch.py`
  - performs a live `511` fetch only if `TRANSIT_511_API_KEY` is configured locally
  - skips cleanly when no token is available or network access to `511` is blocked
  - verifies the fetched archive and provenance metadata are usable by later ingest slices
- `integration/test_511_historic_rg_feed_fetch.py`
  - performs a live monthly historic `511` regional fetch only if `TRANSIT_511_API_KEY` is configured locally
  - skips cleanly when no token is available or network access to `511` is blocked
  - verifies the plain historic regional archive and provenance metadata are usable by later historical ingest slices
- `integration/test_real_dataset_cutover_bundle.py`
  - performs the bounded `B6a` active + historic archive cutover only if `TRANSIT_511_API_KEY` is configured locally
  - reuses `artifacts/cutovers/b6a_real_dataset_cutover_bundle/latest.json` when that manifest is present so validation can rerun against the same archived snapshot
  - when the source archive is regional `RG -so`, the cutover first derives an `SF`-only historic archive and then loads/builds from that reduced snapshot
  - exercises the historic Shapes API fallback path indirectly when the derived archive needs
    geometry backfill before raw GTFS ingest
  - verifies that a second unchanged cutover rerun skips dbt entirely through the manifest-aware no-op guard
  - verifies the rebuilt marts and serving layers expose a broad real Muni route set
  - verifies the live FastAPI contract reads from that rebuilt real dataset rather than the old two-route development cut

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
  - verifies recent monthly archives can omit `shapes.txt` without failing the acquisition step
  - verifies mocked historic fetches write both the zip artifact and JSON provenance metadata
- `unit/test_historic_shapes_api.py`
  - verifies the Shapes API URL and `LineString.pos[]` parser
  - verifies successful shape backfills are cached and reused on repeat runs
- `unit/test_historic_rg_sf_extract.py`
  - verifies SF-only archive derivation preserves retained GTFS and `stop_observations` rows
  - verifies missing historic `shapes.txt` can be backfilled into a synthesized derived archive
  - verifies the build fails when a required `shape_id` cannot be backfilled
- `unit/test_historic_stop_observations_fixture_ingest.py`
  - verifies service-date and observed-arrival timestamp parsing helpers
  - verifies the stop-observations fixture reader preserves required source-facing fields plus typed timestamps
- `unit/test_historic_stop_observations_archive_ingest.py`
  - verifies compact historic service-date parsing and service-day timestamp handling past `24:00:00`
  - verifies `-so` acquisition metadata validation and archive-backed snapshot labeling
- `unit/test_api_contract_fixtures.py`
  - validates the committed API fixture JSON payloads against the same frozen Pydantic response models used by the live FastAPI handlers
- `unit/test_real_dataset_cutover.py`
  - verifies the cutover dbt fingerprint reacts to tracked dbt file or var changes only
  - verifies dbt reuse ignores prior `--skip-dbt` manifests and reuses the last successful matching manifest instead
  - verifies an unchanged cutover rerun skips `run_dbt_run()` entirely and records explicit manifest reuse metadata

Unit test command:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Bundled-runtime alternative:

```powershell
& 'C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests -v
```
