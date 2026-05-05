# Title
S15 API Skeleton

## Goal
Create the Python API service skeleton with health/readiness endpoints and baseline app structure.

## Why this slice exists
The frontend should integrate against a documented API boundary, not pipeline code directly.

## Depends on
- `S03_python_project_bootstrap`
- `S11_metrics_mart_prototype`

## Touches
- API package
- app startup
- health endpoint

## Inputs
- endpoint plan from `05_api_contract.md`

## Outputs
- running API service with health endpoint

## Implementation notes
- keep scope to API bootstrap only
- no business endpoints yet

## Tests required
- health endpoint test
- app startup smoke test

## Acceptance criteria
- API service starts
- health endpoint passes automated test

## Non-goals
- rankings response
- route summaries
- map geometry responses

## Handoff to next slice
Next slice adds the rankings endpoint backed by the first mart.

## Completion notes

