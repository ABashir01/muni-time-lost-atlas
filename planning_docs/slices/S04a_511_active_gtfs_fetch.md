# Title
S04a 511 Active GTFS Fetch

## Goal
Prove the project can fetch the active operator-specific SFMTA/Muni GTFS feed from 511 and land it as an acquisition artifact for later raw ingest.

## Why this slice exists
`S04` proves GTFS-shaped raw ingest with a deterministic fixture. This slice separately proves real 511 acquisition so later slices do not blur network fetch, archive handling, and raw-table loading into one step.

## Depends on
- `S03_python_project_bootstrap`
- `S04_gtfs_static_fixture_ingest`

## Touches
- GTFS acquisition code or scripts
- local acquisition artifact path
- docs describing active-feed fetch behavior

## Inputs
- `planning_docs/03_data_sources.md`
- active operator-specific 511 GTFS endpoint and token usage

## Outputs
- repeatable fetch path for active SFMTA/Muni GTFS from 511
- stored acquisition artifact or acquisition metadata suitable for later raw ingest

## Implementation notes
- keep this slice focused on acquisition, not canonical modeling
- do not merge active operator-specific feed logic with historic regional feed logic
- preserve enough provenance to identify operator, fetch time, and acquisition source

## Tests required
- verify the acquisition code can fetch or validate a GTFS zip from 511 in a controlled way
- verify the fetched artifact or metadata is structurally usable by later ingest work

## Acceptance criteria
- the project has a documented, repeatable path for fetching active Muni GTFS from 511
- later slices do not need to invent active-feed acquisition

## Non-goals
- historic regional feed fetch
- raw-table modeling beyond what already exists
- canonical scheduled models

## Handoff to next slice
`S05_canonical_scheduled_models` should assume active GTFS acquisition is a known upstream step.

## Completion notes
- What changed:
  - added `pipeline/src/muni_lta_pipeline/active_gtfs_fetch.py` to fetch the active operator-specific `511` GTFS feed for `operator_id=SF`
  - added a gitignored local artifact path under `artifacts/acquisitions/511/operator_active/` and documented it in `artifacts/README.md`
  - added `TRANSIT_511_API_KEY` to `.env.example`
  - added unit coverage for URL construction, zip validation, and mocked fetch/archive behavior
  - added an integration test that performs a live `511` fetch only when a local token is configured and network access is available
  - updated project docs and recorded the acquisition-boundary decision in `planning_docs/09_decisions.md`
- Tests run:
  - `& 'C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest tests.unit.test_511_active_gtfs_fetch -v`
  - `& 'C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest tests.integration.test_511_active_gtfs_fetch -v`
  - `& 'C:\Users\ahadb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests -v`
- Results:
  - active acquisition unit tests passed
  - full repository `unittest discover` sweep passed
  - the live `511` integration test skipped because `TRANSIT_511_API_KEY` is not configured locally in this environment
- Follow-up issues:
  - later slices still need to decide when/how the archived active zip is unpacked for raw ingest reuse
  - historic `RG` acquisition remains separate work for `S06a`
