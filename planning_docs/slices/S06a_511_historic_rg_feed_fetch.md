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

