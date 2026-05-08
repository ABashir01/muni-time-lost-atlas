# Title
S06a 511 Historic RG Feed Fetch

## Goal
Prove the project can fetch the historic 511 regional `RG` feed needed for monthly retrospective analysis, including the `-so` path for `stop_observations` when required.

## Why this slice exists
The historical-analysis side of the project depends on 511’s regional historic feed structure, which differs from the active operator-specific feed. This fetch step should be explicit rather than hidden inside the ingest/modeling slices.

## Depends on
- `S03_python_project_bootstrap`
- `S05_canonical_scheduled_models`

## Touches
- historic acquisition code or scripts
- local acquisition artifact path
- docs describing historic regional feed fetch behavior

## Inputs
- `planning_docs/03_data_sources.md`
- 511 historic `RG` feed assumptions and `-so` suffix behavior

## Outputs
- repeatable fetch path for historic regional GTFS
- repeatable fetch path for historic regional GTFS with `stop_observations`
- provenance notes or metadata suitable for later reconciliation

## Implementation notes
- keep this slice focused on acquisition and provenance
- preserve month, feed scope, and `-so` usage explicitly
- do not collapse regional historic IDs into Muni-specific IDs in this slice

## Tests required
- verify the acquisition path handles a requested historic month
- verify the artifact or metadata clearly distinguishes plain historic feed vs historic feed with `stop_observations`

## Acceptance criteria
- the project has a documented, repeatable path for fetching the historic `RG` feed used by analysis slices
- later historical slices do not need to invent acquisition or provenance handling

## Non-goals
- historical raw-table load itself
- scheduled/observed joins
- route metrics

## Handoff to next slice
`S06_historic_stop_observations_ingest` should assume the historic `RG` acquisition path is already known and focus only on parsing/loading.

## Completion notes
- Changed files:
  - `pipeline/src/muni_lta_pipeline/historic_rg_feed_fetch.py`
  - `tests/unit/test_511_historic_rg_feed_fetch.py`
  - `tests/integration/test_511_historic_rg_feed_fetch.py`
  - `pipeline/README.md`
  - `README.md`
  - `tests/README.md`
  - `planning_docs/09_decisions.md`
  - `planning_docs/slices/S06a_511_historic_rg_feed_fetch.md`
- What changed:
  - added a dedicated historic regional `511` acquisition module for `operator_id=RG`
  - implemented explicit support for both `historic=YYYY-MM` and `historic=YYYY-MM-so`
  - preserved provenance for requested month, feed scope, `stop_observations` intent, acquisition timestamp, and requested URL
  - validated the requested archive variant so plain historic requests and `-so` requests remain distinguishable for later slices
  - documented the historic acquisition commands and test coverage in repository docs
  - recorded the historic acquisition boundary decision in `planning_docs/09_decisions.md`
- Tests run:
  - `& 'C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest tests.unit.test_511_historic_rg_feed_fetch -v`
  - `& 'C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest tests.integration.test_511_historic_rg_feed_fetch -v`
- Results:
  - unit tests verify the historic `RG` URL builder, month validation, `stop_observations` variant checks, and mocked acquisition metadata for both plain and `-so` requests
  - the live integration test skips cleanly when no `TRANSIT_511_API_KEY` is configured or network access to `511` is unavailable
  - the slice remains limited to acquisition artifacts and provenance metadata only
- Follow-up issues:
  - later historical ingest slices still need to parse/load the archived `RG` feeds and reconcile regional IDs into downstream Muni-focused models
