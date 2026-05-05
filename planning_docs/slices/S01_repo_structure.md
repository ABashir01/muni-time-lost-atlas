# Title
S01 Repo Structure

## Goal
Create the initial repository structure for the frontend app, API service, pipeline code, tests, fixtures, and planning docs so later slices have clear homes.

## Why this slice exists
All later work depends on stable project layout and predictable directory ownership.

## Depends on
- none

## Touches
- repository root
- top-level directories
- README or bootstrap notes if needed

## Inputs
- stack decisions from `00_project_brief.md`
- boundaries from `04_architecture.md`

## Outputs
- directory structure for frontend, API, pipeline, tests, fixtures, and docs
- minimal bootstrap notes

## Implementation notes
- keep this slice structural only
- do not add real product logic
- directory names should reflect long-term responsibilities clearly

## Tests required
- verify expected directories exist
- verify bootstrap instructions match the created structure

## Acceptance criteria
- repo has clear homes for frontend, API, pipeline, tests, and fixtures
- no downstream slice needs to invent project layout

## Non-goals
- framework initialization
- database setup
- business logic

## Handoff to next slice
Next slice uses this structure to bootstrap Postgres/PostGIS.

## Completion notes

- What changed:
  - created top-level directories: `frontend/`, `api/`, `pipeline/`, `tests/`, and `fixtures/`
  - created subdirectories for `tests/unit`, `tests/integration`, and fixture categories for GTFS static, stop observations, API payloads, and geospatial data
  - added root and per-area README notes to document ownership and intended responsibilities
- Tests run:
  - verified expected directories exist from the repository root
  - verified bootstrap instructions in `README.md` match the created structure
- Results:
  - pass
- Follow-up issues:
  - `S02_database_bootstrap` should decide whether any database-specific local tooling lives under `pipeline/`, `infra/`, or another clearly named location before introducing DB bootstrap files
