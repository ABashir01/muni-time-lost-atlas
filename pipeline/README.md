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

Current archive-backed GTFS raw-load artifact:

- `src/muni_lta_pipeline/gtfs_archive_ingest.py`
  - reads the JSON sidecar and adjacent GTFS zip written by either `active_gtfs_fetch.py` or `historic_rg_feed_fetch.py`
  - loads the fetched archive into `raw.gtfs_*` using archive-backed `snapshot_label` metadata
  - supports `--append` so active and bounded historic snapshots can coexist in raw storage

Example commands:

```powershell
& 'C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\pipeline\src\muni_lta_pipeline\gtfs_archive_ingest.py --metadata-path .\artifacts\acquisitions\511\operator_active\511_operator_active_SF_20260520T184518Z.json
& 'C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\pipeline\src\muni_lta_pipeline\gtfs_archive_ingest.py --metadata-path .\artifacts\acquisitions\511\regional_historic\511_regional_historic_RG_202302_with_so_20260520T184533Z.json --append
```

Current historic archive reduction artifact:

- `src/muni_lta_pipeline/historic_rg_sf_extract.py`
  - derives an `SF`-only historic archive from a fetched `RG -so` source archive
  - preserves loader-compatible metadata plus retained row-count provenance
  - writes the reduced archive under `artifacts/acquisitions/511/regional_historic_sf/`

Example command:

```powershell
& 'C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\pipeline\src\muni_lta_pipeline\historic_rg_sf_extract.py --metadata-path .\artifacts\acquisitions\511\regional_historic\511_regional_historic_RG_202302_with_so_20260520T201335Z.json --agency-id SF
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

Current scheduled/observed join artifact:

- `src/muni_lta_pipeline/canonical_observed_stop_events.py`
  - materializes the first conservative `canonical.observed_stop_events` join for `S07`
  - keeps only exact matches on `service_date`, `trip_id`, `stop_sequence`, and `stop_id`
  - creates audit and summary views so unmatched observations remain visible

Example command:

```powershell
& 'C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\pipeline\src\muni_lta_pipeline\canonical_observed_stop_events.py
```

Current geospatial overlay artifact:

- `src/muni_lta_pipeline/transit_lane_overlay_fixture_ingest.py`
  - creates and loads the first `raw.transit_only_lanes` fixture for `B3`
  - preserves a minimal contextual overlay shape in raw before dbt materializes PostGIS-serving geometry

Example command:

```powershell
& 'C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\pipeline\src\muni_lta_pipeline\transit_lane_overlay_fixture_ingest.py
```

Current GIS + segment artifact:

- `src/muni_lta_pipeline/gis_segment_metrics.py`
  - materializes the dbt graph for route geometry, stop geometry, adjacent-stop segment metrics, and serving map layers
  - keeps the segment strategy explicit as `adjacent_stop_pair`

Example command:

```powershell
& 'C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\pipeline\src\muni_lta_pipeline\gis_segment_metrics.py
```

Current real-dataset cutover artifact:

- `src/muni_lta_pipeline/real_dataset_cutover.py`
  - fetches the active `SF` GTFS plus one bounded historic `RG -so` archive
  - derives an `SF`-only historic archive snapshot from the fetched regional source archive
  - loads the active GTFS archive plus the derived `SF`-only historic archive into raw storage
  - loads the derived `SF`-only `stop_observations` archive into `raw.stop_observations`
  - rebuilds the dbt graph against the reduced `regional_historic_sf` snapshot
  - reuses matching raw snapshots by default on repeat runs so unchanged raw tables are not truncated and reloaded again
  - skips dbt entirely on repeat runs when the raw snapshot labels, cutover dbt vars, and dbt project fingerprint still match the last successful cutover manifest
  - accepts `--force-raw-reload` to bypass raw reuse and `--skip-dbt` for artifact/raw-only preparation
  - writes a provenance manifest under `artifacts/cutovers/b6a_real_dataset_cutover_bundle/`

Example command:

```powershell
& 'C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\pipeline\src\muni_lta_pipeline\real_dataset_cutover.py --historic-month 2023-02 --historic-agency-id SF
```

Exact rerun of the validated archived snapshot:

```powershell
& 'C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' .\pipeline\src\muni_lta_pipeline\real_dataset_cutover.py --historic-month 2023-02 --historic-agency-id SF --active-metadata-path .\artifacts\acquisitions\511\operator_active\511_operator_active_SF_20260520T201312Z.json --historic-metadata-path .\artifacts\acquisitions\511\regional_historic\511_regional_historic_RG_202302_with_so_20260520T201335Z.json
```
