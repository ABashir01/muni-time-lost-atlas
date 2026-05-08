# Title
S06b Real Historic Stop Observations Load

## Goal
Load a real fetched 511 historic regional `RG` archive's `stop_observations.txt` into `raw.stop_observations` so the project has a non-fixture historical raw-load path before join work begins.

## Why this slice exists
`S06a` proves historic archive acquisition and `S06` proves fixture-driven raw ingest shape, but neither one loads a real fetched monthly archive into the database. This slice closes that gap so `S07` can focus on scheduled/observed joins instead of inventing archive-loading behavior.

## Depends on
- `S06a_511_historic_rg_feed_fetch`
- `S06_historic_stop_observations_ingest`

## Touches
- historic archive load code
- raw stop observations ingest path
- archive provenance handling
- tests for loading a real fetched archive

## Inputs
- archived historic `RG` acquisition artifacts from `S06a`
- raw stop observations table and fixture-ingest shape from `S06`
- data-source assumptions in `03_data_sources.md`

## Outputs
- repeatable path to open a fetched historic regional archive
- extracted `stop_observations.txt` rows loaded into `raw.stop_observations`
- preserved provenance linking the raw load to the source archive metadata

## Implementation notes
- keep this slice focused on loading a real fetched archive, not on scheduled/observed joins
- support one real month first; do not optimize for large-scale backfill yet
- preserve the same source-facing observation fields established in `S06`
- keep archive provenance visible enough that later reconciliation/debugging can trace the loaded month and acquisition artifact

## Tests required
- verify a fetched archive with `stop_observations.txt` can be loaded into `raw.stop_observations`
- verify loaded rows preserve required observation fields and typed timestamps
- verify loaded metadata or snapshot labeling distinguishes the real archive load from the fixture load

## Acceptance criteria
- the project can load a real fetched historic `RG` archive into `raw.stop_observations`
- `S07` can assume both scheduled GTFS and real observed arrivals exist in raw tables

## Non-goals
- canonical observed models
- scheduled/observed join logic
- route metrics
- multi-month production backfill strategy

## Handoff to next slice
`S07_scheduled_observed_join` should assume real historic observed arrivals can be loaded from an archived `RG` month and should focus only on joining scheduled and observed stop events.

## Completion notes
- Added `pipeline/src/muni_lta_pipeline/historic_stop_observations_archive_ingest.py` to load real fetched `RG` `-so` archives into `raw.stop_observations` using the S06a `.json` sidecar as the provenance entrypoint.
- Preserved the S06 raw observation shape by mapping real archive `to_stop_id` into `stop_id`, parsing compact `service_date` values, deriving typed `observed_arrival_ts` from local service-day times, and labeling archive-backed loads as `archive_<artifact_stem>`.
- Updated the raw stop-observations DDL to stop dropping the table during setup so fixture and archive loads can coexist when the real archive path is run with append semantics for provenance checks.
- Added unit coverage for compact historic date parsing, post-midnight service-day times, and `-so` metadata validation plus a live integration test that fetches one real month, loads bounded archive rows, and verifies snapshot labels remain distinct from fixture rows.
- Updated repository, test, data-source, data-model, and decision docs for the real historic archive ingest path and its source-to-raw field mapping.
