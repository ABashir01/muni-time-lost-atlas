# Title
S03 Python Project Bootstrap

## Goal
Create the Python project foundations for the pipeline and API code, including test tooling and import structure.

## Why this slice exists
Later ETL, metrics, and API slices need a clean Python package layout and repeatable test runner.

## Depends on
- `S01_repo_structure`
- `S02_database_bootstrap`

## Touches
- Python package structure
- dependency configuration
- test runner configuration

## Inputs
- architecture in `04_architecture.md`

## Outputs
- pipeline package skeleton
- API package skeleton
- working unit test harness

## Implementation notes
- keep this slice to bootstrap and tooling
- do not implement GTFS parsing or HTTP endpoints yet

## Tests required
- one passing placeholder unit test
- import smoke test for both major Python packages

## Acceptance criteria
- Python tooling is runnable
- test harness works
- package structure is stable enough for later slices

## Non-goals
- endpoint behavior
- data modeling
- database schemas beyond connection readiness

## Handoff to next slice
Next slice ingests a tiny GTFS static fixture.

## Completion notes

