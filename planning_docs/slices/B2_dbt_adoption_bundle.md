# Title
B2 dbt Adoption Bundle

## Goal
Migrate the proven SQL transformation chain into a real dbt project.

## Why this bundle exists
dbt is part of the intended analytics-engineering signal, but it should be introduced only after the first metrics graph is stable enough to migrate once.

## Depends on
- `B1_core_metrics_bundle`

## Touches
- dbt project scaffolding
- dbt source declarations
- dbt staged/canonical/mart models
- dbt-native model tests

## Inputs
- existing proven SQL logic for:
  - scheduled models
  - observed join models
  - first metric marts
- architecture guidance in `04_architecture.md`

## Outputs
- dbt project in-repo
- dbt-based staged/canonical/mart graph
- dbt-native model tests for core entities

## Implementation notes
- dbt starts where data is already in Postgres
- dbt does not replace Python fetch/load code
- keep dbt focused on transformation and tests, not orchestration
- migrate the proven SQL graph; do not redesign the data model in this bundle
- organize models into:
  - `staging`
  - `canonical`
  - `marts`
- add dbt-native tests for:
  - unique keys
  - not-null keys
  - core relationships

## Tests required
- one primary dbt build/test pass covering the staged/canonical/mart graph
- one regression check proving the API-facing metric tables still match prior semantics

## Acceptance criteria
- dbt can build the staged/canonical/mart graph successfully
- core dbt tests pass
- the migrated graph preserves the established metric contract

## Non-goals
- new metrics
- API work
- frontend work
- realtime work

## Handoff to next bundle
`B3_gis_segment_metrics_bundle` should build map-serving and segment outputs on top of the stabilized transformation graph.

## Completion notes
- what changed
  - added a real in-repo dbt project under `dbt/` with raw source declarations, schema-selection macros, and a generic composite-key uniqueness test
  - migrated the proven scheduled, observed-join, and first-mart SQL graph into dbt `staging`, `canonical`, and `marts` models without changing the accepted metric semantics
  - rewired the existing Python transformation entrypoints to call dbt build selectors so raw acquisition/load code stays in Python and downstream tests keep the same interface
  - added dbt-native unique, not-null, and relationship tests on the core canonical and mart models
- what tests were run
  - `.\.venv\Scripts\python.exe -m unittest tests.integration.test_core_metrics_bundle -v`
- what passed
  - the dbt staged/canonical/mart graph built successfully against the local Postgres setup
  - dbt-native tests passed during the build
  - the route-window, route-direction, and route-hour summaries preserved the previously accepted waiting-loss and in-vehicle-loss semantics
- any known limitations or follow-up issues
  - local environments with an older persisted Postgres volume may need the DB user password realigned with the repo `.env` before host-side dbt connections succeed
  - the legacy SQL files under `db/sql/` remain in the repo as historical references, but the active transformation path now runs through dbt
