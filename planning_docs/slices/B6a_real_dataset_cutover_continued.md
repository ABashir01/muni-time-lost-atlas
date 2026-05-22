# Title
B6a Real Dataset Cutover Continued

## Why this follow-up exists
`B6a` is functionally complete for the real bounded dataset cutover, but local rebuild cost is still higher than ideal because the dbt graph still fully rematerializes large observed/scheduled models on repeat runs.

This note is the handoff for the next agent/orchestrator step.

## Current status
Completed in `B6a`:
- real active GTFS acquisition path is in use
- real historic `RG -so` acquisition path is in use
- raw GTFS archive loader exists and is used
- raw historic stop-observations archive loader exists and is used
- bounded historical snapshot is documented and reproducible
- app-facing marts/API/frontend are no longer effectively limited to routes `14` and `49`
- route-detail frontend was fixed for real namespaced route ids such as `SF:49`
- a derived `SF`-only historic archive path now exists:
  - `pipeline/src/muni_lta_pipeline/historic_rg_sf_extract.py`
- repeat cutovers now reuse unchanged raw snapshots by default:
  - `pipeline/src/muni_lta_pipeline/real_dataset_cutover.py`
  - override flags:
    - `--force-raw-reload`
    - `--skip-dbt`

## Validated bounded snapshot
- historic month: `2023-02`
- source historic feed: `RG -so`
- derived app-facing historic feed scope: `regional_historic_sf`
- selected agency id: `SF`

Validated local artifacts:
- source regional metadata:
  - `artifacts/acquisitions/511/regional_historic/511_regional_historic_RG_202302_with_so_20260520T201335Z.json`
- derived `SF`-only metadata:
  - `artifacts/acquisitions/511/regional_historic_sf/511_regional_historic_RG_202302_with_so_20260520T201335Z_SF_only.json`
- latest cutover manifest:
  - `artifacts/cutovers/b6a_real_dataset_cutover_bundle/latest.json`

## Measured timings
Measured on the validated local machine:
- prior cached full-regional cutover: about `16.1 min`
- first `SF`-only archive derivation pass: about `145 s`
- cached `SF`-only cutover before raw snapshot reuse: about `10.4 min`
- repeat `SF`-only cutover with raw snapshot reuse enabled: about `8.7 min`

Interpretation:
- the unnecessary raw replacement problem was real and is now materially reduced
- the remaining dominant cost is the dbt rebuild itself

## What changed already
### Source/data-volume reduction
The source regional archive is still fetched from `511`, but the app-facing build now uses a smaller derived `SF`-only historic archive.

Observed retained counts in the derived archive:
- `routes.txt = 65`
- `trips.txt = 115384`
- `stop_times.txt = 4364383`
- `stops.txt = 3281`
- `shapes.txt = 122044`
- `calendar_dates.txt = 1924712`
- `stop_observations.txt = 4734308`

### Raw reuse
Repeat cutovers now skip reloading:
- `raw.gtfs_*`
- `raw.stop_observations`
- `raw.transit_only_lanes`

when the target snapshot labels are already present.

## Remaining bottleneck
The remaining issue is no longer raw artifact fetch/load. It is the dbt rebuild.

In plain terms:
- dbt still rebuilds the large staged/canonical/mart graph from scratch on each cutover run
- the most expensive work is building the large event-level scheduled/observed tables and unmatched-resolution intermediates

Heavy dbt models observed during rebuild:
- `stg_stop_observations`
- `scheduled_stop_events`
- `observed_stop_events`
- `int_unmatched_resolved`
- `route_stop_segments`

The final route summary table is not the expensive part. The expensive part is rebuilding the large detailed event graph that feeds it.

## Recommended next work
Best-practice next step:
- add a dbt no-op guard so dbt is skipped entirely when:
  - the raw snapshot labels are unchanged
  - the dbt vars are unchanged
  - the dbt project fingerprint is unchanged

Recommended implementation shape:
1. compute and store a dbt fingerprint in the cutover manifest
2. fingerprint should include:
   - `dbt/models/**`
   - `dbt/macros/**`
   - `dbt_project.yml`
   - cutover dbt vars
3. on repeat cutover:
   - compare current raw snapshot labels
   - compare current dbt vars
   - compare current dbt fingerprint
4. if all match the last successful manifest:
   - skip dbt
   - report reuse in the manifest/log

## Secondary follow-up after the no-op guard
If more performance work is still needed after the no-op guard:
- add partial dbt rebuild support for developer workflows
- consider incremental materialization for:
  - `stg_stop_observations`
  - `observed_stop_events`
  - possibly `scheduled_stop_events`
  - possibly `int_unmatched_resolved`

## Why this matters
This no longer materially affects user request latency directly. API read timings were already fast. The remaining cost matters operationally:
- local rebuild iteration speed
- repeatability of dataset publication
- ease of correcting/revalidating the bounded historical snapshot

## Suggested handoff instruction
Suggested instruction for the next agent/orchestrator:

`Continue B6a operational follow-up from planning_docs/slices/B6a_real_dataset_cutover_continued.md. The real bounded cutover is complete. Do not revisit source acquisition or SF-only archive extraction unless needed. Focus on adding a manifest-aware dbt no-op guard and only rebuild dbt when raw snapshot ids, dbt vars, or dbt project fingerprint changed. Validate that repeat runs skip dbt entirely when nothing changed.`
