# Title
B6a Real Dataset Cutover Bundle

## Goal
Replace the constrained two-route development dataset with a real historical 511-backed dataset for the app-facing marts, API, and frontend.

## Why this bundle exists
The product now proves the plumbing, transformations, API, and frontend, but the visible user experience is still too tied to the development cut. This bundle makes the app look like a real Muni product instead of a two-route demo.

## Depends on
- `B6_frontend_api_integration_bundle`
- real active GTFS acquisition path
- real historic RG archive acquisition path
- real historic stop-observations raw load path
- the existing acquisition/load scripts:
  - `pipeline/src/muni_lta_pipeline/active_gtfs_fetch.py`
  - `pipeline/src/muni_lta_pipeline/historic_rg_feed_fetch.py`
  - `pipeline/src/muni_lta_pipeline/historic_stop_observations_archive_ingest.py`

## Touches
- Python acquisition/load orchestration
- raw GTFS raw-load path for real downloaded archives, not just fixtures
- dbt staged/canonical/mart rebuild path
- API read surface only if a published route-coverage or direction-coverage clarification is required
- frontend only for tiny copy/state adjustments if the larger dataset exposes new empty or mismatch conditions

## Inputs
- real active 511 scheduled GTFS zip + metadata artifacts fetched by `active_gtfs_fetch.py`
- one or more real historic RG `-so` zip + metadata artifacts fetched by `historic_rg_feed_fetch.py`
- accepted dbt transformation graph
- accepted historical/static API surface

## Outputs
- app-facing route rankings, route detail, compare, and map views backed by a real larger route set
- explicit documentation of the selected historical month or historical window used for the cutover
- deterministic local/dev instructions for rebuilding the cutover dataset
- a scripted, reproducible path from `511` endpoint fetch -> raw-table population -> dbt build -> API/frontend consumption

## Implementation notes
- choose a bounded real historical scope first, such as one representative month, before attempting multi-month breadth
- prefer a reproducible "cutover snapshot" over an ambiguous rolling state for the first pass
- do not hand-wave the data cutover as a manual one-off; use the existing `511` fetch scripts and their archived outputs as the source of truth
- explicitly fetch the real inputs from the `511` endpoints with:
  - `active_gtfs_fetch.py` for current scheduled GTFS
  - `historic_rg_feed_fetch.py --with-stop-observations` for historic observed data
- populate the database from those fetched artifacts instead of fixture-only inputs
- if the current active GTFS raw-load path is still too fixture-oriented, extend or replace it with a real archive loader as part of this bundle
- keep provenance intact by preserving the acquisition metadata JSON sidecars and threading the chosen snapshot labels through the raw-load step
- document exactly which month(s), operator scope, and archive variants are used
- validate that the app no longer surfaces only routes `14` and `49` unless the selected month genuinely yields that result
- keep the product language honest about any remaining route/detail asymmetries
- if route-detail directional coverage is still uneven, keep the UI state explicit instead of masking it
- expected execution shape:
  1. fetch active GTFS from `511`
  2. fetch one bounded historic `RG -so` archive from `511`
  3. load the active GTFS archive into `raw.gtfs_*`
  4. load the historic `stop_observations` archive into `raw.stop_observations`
  5. run dbt to rebuild `staging`, `canonical`, `marts`, and `serving`
  6. verify the API and frontend against that rebuilt real dataset

## Tests required
- one primary integration run that proves the real dataset builds the app-facing marts
- one API contract run against the rebuilt real dataset
- one frontend smoke pass against the real dataset-backed API
- one reproducibility check that the documented fetch/load commands recreate the same bounded cutover snapshot shape locally

## Acceptance criteria
- homepage rankings show a broader real route set
- compare is no longer practically limited to the original two-route development cut
- map and route detail reflect the real dataset-backed API surface
- the selected historical scope is documented clearly enough to rebuild locally
- the cutover instructions explicitly reference the real `511` fetch scripts and the raw-load steps that populate Postgres from their outputs

## Non-goals
- realtime vehicle overlays
- changing the public metric definitions
- redesigning the frontend

## Handoff to next bundle
After `B6a`, proceed to `B6b_real_map_engine_bundle` if the schematic map should be replaced before realtime, or continue directly to `B7` only if the schematic is explicitly accepted as sufficient.
