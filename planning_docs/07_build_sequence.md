# Build Sequence

## Build Strategy
Build the remaining MVP in larger subsystem bundles instead of narrow feature slices.

From this point forward:
1. finish the core metric/data path
2. migrate the proven SQL graph into dbt
3. build the full historical/static API
4. build the full frontend against fixtures
5. integrate frontend + API
6. operationalize rolling historical publication after the historical product works

## Completed Work
These slices are complete and remain part of the permanent project history:
- `S01_repo_structure`
- `S02_database_bootstrap`
- `S03_python_project_bootstrap`
- `S03a_schema_strategy`
- `S04_gtfs_static_fixture_ingest`
- `S04a_511_active_gtfs_fetch`
- `S05_canonical_scheduled_models`
- `S06a_511_historic_rg_feed_fetch`
- `S06_historic_stop_observations_ingest`
- `S06b_real_historic_stop_observations_load`
- `S07_scheduled_observed_join`

The current baseline now includes:
- raw GTFS ingest
- active `511` acquisition
- historic `RG` acquisition
- fixture and real historic stop-observations load
- canonical scheduled models
- first conservative scheduled/observed join

## Remaining Bundles
### B1 Core Metrics Bundle
- goal: produce the first route-level rider-time-loss metrics from the joined data
- replaces: `S08`, `S09`, `S10`, and most of `S11`
- doc: [B1_core_metrics_bundle.md](./slices/B1_core_metrics_bundle.md)

### B2 dbt Adoption Bundle
- goal: migrate the proven SQL transformation graph into a real dbt project
- replaces: the previously implicit dbt introduction
- doc: [B2_dbt_adoption_bundle.md](./slices/B2_dbt_adoption_bundle.md)

### B3 GIS And Segment Metrics Bundle
- goal: add geometry-serving tables, transit-lane overlay context, and the first segment metric layer
- replaces: `S12`, `S13`, `S14`
- doc: [B3_gis_segment_metrics_bundle.md](./slices/B3_gis_segment_metrics_bundle.md)

### B3a Stop Wait Metrics Bundle
- goal: add stop-based waiting-loss metrics as a separate spatial layer instead of forcing waiting loss into segment metrics
- replaces: the currently implicit future extension of `B1`/`B3`
- doc: [B3a_stop_wait_metrics_bundle.md](./slices/B3a_stop_wait_metrics_bundle.md)

### B4 API Bundle
- goal: build the full historical/static FastAPI surface in one pass
- replaces: `S15` through `S19`
- doc: [B4_api_bundle.md](./slices/B4_api_bundle.md)

### B4a Stop Wait API Extension
- goal: expose stop-based waiting hotspots through a dedicated historical/static API endpoint
- replaces: the currently deferred stop-wait endpoint follow-up from `B4`
- doc: [B4a_stop_wait_api_extension.md](./slices/B4a_stop_wait_api_extension.md)

### B5a Homepage Visual Lock
- goal: match the approved homepage mockup at the primary desktop breakpoint before broader frontend acceptance
- replaces: the currently unstable homepage portion of `B5`
- doc: [B5a_homepage_visual_lock.md](./slices/B5a_homepage_visual_lock.md)

### B5b Frontend Static Surface Completion
- goal: finish the remaining static fixture-driven frontend surfaces once the homepage design is locked
- replaces: the remainder of `B5` and legacy `S20` through `S25`
- doc: [B5b_static_surface_completion.md](./slices/B5b_static_surface_completion.md)

### B6 Frontend API Integration Bundle
- goal: wire the finished frontend to the live historical/static API
- replaces: `S26` through `S29`
- doc: [B6_frontend_api_integration_bundle.md](./slices/B6_frontend_api_integration_bundle.md)

### B6a Real Dataset Cutover Bundle
- goal: replace the controlled two-route development dataset with a real historical 511-backed cutover dataset for the app-facing marts and API
- replaces: the currently implicit jump from validated development fixtures to production-like historical coverage
- doc: [B6a_real_dataset_cutover_bundle.md](./slices/B6a_real_dataset_cutover_bundle.md)

### B6b Real Map Engine Bundle
- goal: replace the homepage and route/map schematic surfaces with a real interactive map engine while preserving the accepted visual hierarchy
- replaces: the currently implicit map-library migration
- doc: [B6b_real_map_engine_bundle.md](./slices/B6b_real_map_engine_bundle.md)

### B6c Historic Shapes API Fallback
- goal: backfill missing historic `shapes.txt` during recent monthly cutovers by
  using the 511 Shapes API in the build step
- exists because recent `RG -so` archives can omit `shapes.txt` while still
  carrying schedule and observed-arrival data needed for the metrics
- doc: [B6c_historic_shapes_api_fallback.md](./slices/B6c_historic_shapes_api_fallback.md)

### B7 Rolling Historical Publication Bundle
- goal: publish a rolling 6-month historical window and refresh it monthly
- replaces: `S30` through `S32`
- doc: [B7_realtime_bundle.md](./slices/B7_realtime_bundle.md)

### B8 Product Hardening Bundle
- goal: polish, explain, and harden the MVP for public and portfolio use
- replaces: `S33` through `S35`
- doc: [B8_product_hardening_bundle.md](./slices/B8_product_hardening_bundle.md)

## Post-MVP Follow-Ups
These do not belong on the current MVP critical path.

### P1 Directional Public Shift
- goal: move the public ranking and map unit from route-level to route-direction-level everywhere public
- scope: homepage, rankings, map, and route-detail entry behavior
- doc: [P1_directional_public_shift.md](./slices/P1_directional_public_shift.md)

### P2 Directional Compare Shift
- goal: make compare direction-aware after the public ranking/map shift is complete
- scope: compare selector, compare API contract, compare cards
- doc: [P2_directional_compare_shift.md](./slices/P2_directional_compare_shift.md)

## Legacy Future Slices
The old fine-grained future slices `S08` through `S35` are now superseded by bundles `B1` through `B8`.

Keep the old slice docs only as planning history. Do not resume implementation from those legacy slice docs unless a bundle is intentionally split again later.

## Phase Gates
### Before B2
- the joined scheduled/observed path is stable
- the first route-level metrics exist in SQL-first form
- metric names and semantics are stable enough to migrate once

### Before B4
- the first marts exist and are queryable
- the route/segment data contract is stable enough for API response models
- stop-based waiting metrics exist or are explicitly deferred from the first API response shapes

### Before B6
- API response shapes are frozen in docs and code
- `B5a` homepage visual lock is accepted
- fixture payloads exist for every frontend surface
- `B5b` static surface completion is accepted
- if route-detail stop-wait hotspots are intended in the first live integration pass, `B4a` is complete

### Before B7
- `B6a` real dataset cutover is complete so the app is no longer limited to the tiny development route set
- `B6b` real map engine cutover is complete if realtime will be shown on an actual map rather than a schematic placeholder
- `B6c` historic shapes fallback is complete if recent monthly archives needed
  for rolling publication may omit `shapes.txt`
- the historical/static product is complete and trustworthy without realtime
- map and route detail screens already work from static/historical data
- deployment strategy and live retention-window choice are explicit

### Before B8
- `B7` rolling publication exists and can refresh the app monthly without manual ad hoc rebuilds

## Validation Standard
Use lean validation for all future bundles:
- one primary test suite per bundle
- one regression suite only when the bundle materially touches a prior subsystem
- live `511` checks only when the bundle directly depends on live `511` behavior
- DB-mutating integration suites must be run sequentially, never in parallel, against the shared local Postgres instance

Use full `unittest discover` or broader regression sweeps only at major checkpoints:
- after `B2`
- after `B4`
- after `B6`
- after `B8`

After the MVP path:
- treat `P1` and `P2` as explicit follow-up work, not as implicit cleanup
- keep the current route-level public behavior only so long as the methodology
  disclosure remains explicit
