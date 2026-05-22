# B6a Real Dataset Cutover Snapshot

Bounded historical cut:
- historic month: `2023-02`
- historic archive scope: `RG -so`
- in-archive agency filter for app-facing marts: `SF`
- derived app-facing historic feed scope: `regional_historic_sf`
- active GTFS provenance snapshot validated in this bundle: `511_operator_active_SF_20260520T201312Z.zip`
- historic GTFS + observations provenance snapshot validated in this bundle: `511_regional_historic_RG_202302_with_so_20260520T201335Z.zip`
- derived SF-only historic snapshot validated in this bundle: `511_regional_historic_RG_202302_with_so_20260520T201335Z_SF_only.zip`

Cutover command:

```powershell
$env:PYTHONPATH='C:\Users\ahadb\Documents\New project 3\pipeline\src'
.\.venv\Scripts\python.exe -m muni_lta_pipeline.real_dataset_cutover --historic-month 2023-02 --historic-agency-id SF
```

Exact reproducible rerun against the validated archived artifacts:

```powershell
$env:PYTHONPATH='C:\Users\ahadb\Documents\New project 3\pipeline\src'
.\.venv\Scripts\python.exe -m muni_lta_pipeline.real_dataset_cutover --historic-month 2023-02 --historic-agency-id SF --active-metadata-path 'C:\Users\ahadb\Documents\New project 3\artifacts\acquisitions\511\operator_active\511_operator_active_SF_20260520T201312Z.json' --historic-metadata-path 'C:\Users\ahadb\Documents\New project 3\artifacts\acquisitions\511\regional_historic\511_regional_historic_RG_202302_with_so_20260520T201335Z.json'
```

Raw/archive commands used by the cutover entrypoint:

```powershell
$env:PYTHONPATH='C:\Users\ahadb\Documents\New project 3\pipeline\src'
.\.venv\Scripts\python.exe -m muni_lta_pipeline.active_gtfs_fetch
.\.venv\Scripts\python.exe -m muni_lta_pipeline.historic_rg_feed_fetch --historic-month 2023-02 --with-stop-observations
.\.venv\Scripts\python.exe -m muni_lta_pipeline.historic_rg_sf_extract --metadata-path .\artifacts\acquisitions\511\regional_historic\511_regional_historic_RG_202302_with_so_20260520T201335Z.json --agency-id SF
.\.venv\Scripts\python.exe -m muni_lta_pipeline.gtfs_archive_ingest --metadata-path .\artifacts\acquisitions\511\operator_active\511_operator_active_SF_20260520T201312Z.json
.\.venv\Scripts\python.exe -m muni_lta_pipeline.gtfs_archive_ingest --metadata-path .\artifacts\acquisitions\511\regional_historic_sf\511_regional_historic_RG_202302_with_so_20260520T201335Z_SF_only.json --append
.\.venv\Scripts\python.exe -m muni_lta_pipeline.historic_stop_observations_archive_ingest --metadata-path .\artifacts\acquisitions\511\regional_historic_sf\511_regional_historic_RG_202302_with_so_20260520T201335Z_SF_only.json
```

dbt selection used for the app-facing build:

```json
{
  "gtfs_feed_scope": "regional_historic_sf",
  "gtfs_snapshot_label": "archive_511_regional_historic_RG_202302_with_so_20260520T201335Z_SF_only",
  "historic_agency_id": "SF",
  "observed_feed_scope": "regional_historic_sf",
  "observed_snapshot_label": "archive_511_regional_historic_RG_202302_with_so_20260520T201335Z_SF_only"
}
```

Provenance manifest:
- latest manifest path: `artifacts/cutovers/b6a_real_dataset_cutover_bundle/latest.json`
- timestamped manifest path: `artifacts/cutovers/b6a_real_dataset_cutover_bundle/<timestamp>.json`
- validated latest manifest counts after the successful cutover:
  - `route_count_with_metrics = 65`
  - `map_route_count = 65`
  - top routes begin with `SF:49`, `SF:31`, `SF:F`, `SF:43`, `SF:27`
- derived archive retained rows:
  - `routes.txt = 65`
  - `trips.txt = 115384`
  - `stop_times.txt = 4364383`
  - `stops.txt = 3281`
  - `shapes.txt = 122044`
  - `calendar_dates.txt = 1924712`
  - `stop_observations.txt = 4734308`
- measured rebuild timings on the validated local machine:
  - prior full-regional cached rebuild: about `16.1` minutes
  - first SF-only derivation pass: about `145` seconds
  - cached SF-only rebuild after the derived archive exists: about `10.4` minutes
  - repeat SF-only cutover with raw snapshot reuse enabled: about `8.7` minutes

Raw-reuse note:
- repeated runs of `real_dataset_cutover.py` now reuse matching raw GTFS, raw observations, and overlay snapshots automatically when the requested snapshot labels are already present
- repeated runs also skip dbt entirely when the raw snapshot labels, cutover dbt vars, and tracked dbt project files still match the last successful cutover manifest
- the cutover manifest now records `dbt_action`, `reused_existing_dbt`, `dbt_reuse_manifest_path`, and a `dbt_fingerprint` covering `dbt/models/**`, `dbt/macros/**`, `dbt_project.yml`, and the cutover dbt vars
- use `--force-raw-reload` only when you intentionally want to replace the raw snapshot contents
- use `--skip-dbt` when you only need to prepare artifacts/raw inputs without rebuilding the dbt graph yet

Historic archive normalization note:
- the `RG -so` observed rows for Muni carry trip/service ids dated one day ahead of the raw `service_date` field
- the dbt staging model corrects that one-day offset only when the trip-id suffix proves it, so the scheduled/observed join stays explicit and reproducible
