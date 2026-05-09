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
