# Pipeline

Reserved for ingestion, normalization, transformation, and metric computation code.

Current package layout:

- `src/muni_lta_pipeline/__init__.py`
  - package marker and version
- `src/muni_lta_pipeline/config.py`
  - environment-driven config bootstrap

Expected future ownership:

- GTFS static ingest
- historic stop observation ingest
- GTFS-RT ingest later
- dbt project and transformations
- metric computation helpers

Current GTFS static ingest artifact:

- `src/muni_lta_pipeline/gtfs_static_fixture_ingest.py`
  - creates the accepted `raw.gtfs_*` tables for `S04`
  - loads the tiny deterministic GTFS fixture under `fixtures/gtfs_static/minimal`
  - uses the local Docker Compose Postgres/PostGIS service via `psql`

Example command:

```powershell
& 'C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\pipeline\src\muni_lta_pipeline\gtfs_static_fixture_ingest.py
```

Current active-feed acquisition artifact:

- `src/muni_lta_pipeline/active_gtfs_fetch.py`
  - fetches the active operator-specific `511` GTFS zip for `operator_id=SF`
  - validates that the archive contains the required GTFS files for later ingest
  - writes a timestamped `.zip` plus adjacent JSON provenance metadata
  - keeps acquisition separate from raw-table loading

Example command:

```powershell
& 'C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\pipeline\src\muni_lta_pipeline\active_gtfs_fetch.py
```

Current historic regional acquisition artifact:

- `src/muni_lta_pipeline/historic_rg_feed_fetch.py`
  - fetches monthly historic `511` regional GTFS zips for `operator_id=RG`
  - supports both plain historic requests and the `-so` variant that includes `stop_observations.txt`
  - validates the requested variant and writes timestamped zip + JSON provenance metadata
  - keeps historic acquisition separate from any raw-table load or Muni-only filtering

Example commands:

```powershell
& 'C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\pipeline\src\muni_lta_pipeline\historic_rg_feed_fetch.py --historic-month 2023-02
& 'C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\pipeline\src\muni_lta_pipeline\historic_rg_feed_fetch.py --historic-month 2023-02 --with-stop-observations
```

Current scheduled canonical-model artifact:

- `src/muni_lta_pipeline/canonical_scheduled_models.py`
  - materializes the first `staging` and `canonical` scheduled GTFS tables for `S05`
  - expands `service_date` values from `calendar.txt` plus `calendar_dates.txt`
  - normalizes stop times into both `*_time_text` and `*_secs` fields
  - creates:
    - `canonical.scheduled_routes`
    - `canonical.scheduled_trips`
    - `canonical.scheduled_stops`
    - `canonical.service_dates`
    - `canonical.scheduled_stop_events`

Example command:

```powershell
& 'C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\pipeline\src\muni_lta_pipeline\canonical_scheduled_models.py
```

Current historic stop observations ingest artifact:

- `src/muni_lta_pipeline/historic_stop_observations_fixture_ingest.py`
  - creates and loads the first `raw.stop_observations` fixture for `S06`
  - parses typed observed-arrival timestamps while preserving source-facing observation fields
  - keeps historical observation ingest separate from scheduled/observed joins and canonical observed models

Example command:

```powershell
& 'C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\pipeline\src\muni_lta_pipeline\historic_stop_observations_fixture_ingest.py
```
