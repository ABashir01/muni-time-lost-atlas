# B7 Rolling Historical Publication

## Purpose
Operate the live app database as a rolling 6-month historical publication window.

This runbook assumes:
- `Hetzner + Coolify` or equivalent single-VPS deployment
- a scheduled monthly maintenance window
- no realtime vehicle overlays
- the accepted `B6a` cutover path and `B6c` Shapes API fallback are already in place

## Storage Retention

`B7` now owns its own publication-scoped artifact roots under:

- `artifacts/publications/b7_rolling_historical_publication/acquisitions/operator_active`
- `artifacts/publications/b7_rolling_historical_publication/acquisitions/regional_historic`
- `artifacts/publications/b7_rolling_historical_publication/acquisitions/regional_historic_sf`
- `artifacts/publications/b7_rolling_historical_publication/acquisitions/regional_historic_sf_publication`

After each successful bootstrap or advance run, the publication job prunes those roots so they only retain:
- the current active GTFS acquisition
- the current 6 retained monthly historic source artifacts
- the current 6 retained monthly derived `SF` artifacts
- the current combined rolling-window archive
- the latest publication manifest
- the latest cutover manifest/log pair

This keeps on-disk publication storage bounded instead of growing forever.

## New Entry Points

All commands below should be run from:

```powershell
C:\Users\ahadb\Documents\New project 3
```

with:

```powershell
$env:PYTHONPATH='C:\Users\ahadb\Documents\New project 3\pipeline\src'
```

### 1. Daily availability check

Use this during the daily cron window starting on the 2nd of each month:

```powershell
.\.venv\Scripts\python.exe -m muni_lta_pipeline.rolling_historical_publication check-newest-available
```

Expected behavior:
- checks the newest completed month, not the current month
- uses a lightweight probe against `511` `RG -so`
- returns `available=false` cleanly when the next completed month is not yet published

### 2. First production bootstrap

Use this once when initially populating the live 6-month window:

```powershell
.\.venv\Scripts\python.exe -m muni_lta_pipeline.rolling_historical_publication bootstrap-window
```

Expected behavior:
1. determine the newest completed month currently available from `511`
2. derive the trailing 6-month window ending at that month
3. fetch and derive each monthly `SF` archive
4. synthesize one combined rolling-window historic archive
5. rebuild the live app DB from:
   - current active GTFS
   - combined rolling historic archive
6. write:
   - publication manifest under `artifacts/publications/b7_rolling_historical_publication/`
   - cutover manifest/logs under `artifacts/publications/b7_rolling_historical_publication/cutovers/`

### 3. Steady-state monthly advance

Use this after the initial bootstrap succeeds:

```powershell
.\.venv\Scripts\python.exe -m muni_lta_pipeline.rolling_historical_publication advance-window
```

Expected behavior:
- reads the current rolling-publication manifest
- checks whether a newer completed month is now available
- exits cleanly with `action=unavailable` when it is not
- exits cleanly with `action=already_published` when the newest available month is already live
- rebuilds the rolling 6-month publication window when a newer month becomes available

## Current Publication Shape

The implementation keeps the live DB to a rolling 6-month window by rebuilding from a single synthetic publication archive.

That means:
- the live serving DB does **not** keep older months beyond the retained window
- retention is enforced by the rebuild itself, not by incremental in-place pruning

## Combined Archive Strategy

`B7` does not ask dbt to read six separate monthly snapshot labels directly.

Instead it:
- derives one `SF` archive per month
- namespaces month-scoped `trip_id`, `service_id`, and `shape_id` values to avoid cross-month collisions
- keeps the latest route/stop presentation rows when those IDs repeat across months
- concatenates observations and schedule rows into one synthetic 6-month historic archive

This lets the accepted single-snapshot cutover path keep working without a broader dbt join-key refactor.

## Operational Caveat

With the current MVP deployment shape, publication still rebuilds the live DB in place.

Operational implication:
- expect a scheduled monthly maintenance window during bootstrap and monthly publication
- use a low-traffic overnight window on the VPS

## Latest Lightweight Source Verification

Validated recent-month check:

```powershell
.\.venv\Scripts\python.exe -m muni_lta_pipeline.rolling_historical_publication check-newest-available --current-date 2026-05-24
```

Observed result:
- `historic_month = 2026-04`
- `available = true`
