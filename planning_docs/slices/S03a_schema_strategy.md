# Title
S03a Schema Strategy

## Goal
Lock the initial Postgres schema strategy before GTFS ingest begins.

## Why this slice exists
The project does not need the full final database schema yet, but it does need a stable modeling strategy so `S04` and `S05` do not invent table layout ad hoc.

## Depends on
- `S02_database_bootstrap`
- `S03_python_project_bootstrap`

## Touches
- `planning_docs/06_data_model.md`
- `planning_docs/09_decisions.md` if a new modeling decision is formalized
- this slice doc

## Inputs
- `planning_docs/03_data_sources.md`
- `planning_docs/04_architecture.md`
- `planning_docs/06_data_model.md`
- the GTFS/historical modeling requirements from the methodology and product docs

## Outputs
- chosen schema/layer names
- initial raw GTFS table list
- initial canonical scheduled table list
- naming conventions for keys, service dates, timestamps, and geometry columns

## Implementation notes
- this is a planning and modeling slice, not a broad schema implementation slice
- define only what `S04` and `S05` need
- prefer simple, stable naming over speculative completeness
- include enough guidance that ingest/model agents do not make structural decisions on their own

## Tests required
- confirm `planning_docs/06_data_model.md` names the schema layers and first expected entities clearly
- confirm `S04` and `S05` can proceed without inventing database namespaces or canonical table shapes

## Acceptance criteria
- the project has a documented initial DB schema strategy
- `S04` and `S05` have clear guidance on raw vs canonical table boundaries
- no major namespace or naming-convention decision is left to the implementer

## Non-goals
- full final mart design
- segment schema perfection
- realtime schema design
- production migration implementation

## Handoff to next slice
`S04_gtfs_static_fixture_ingest` should use the chosen raw schema strategy, and `S05_canonical_scheduled_models` should use the chosen canonical model names and conventions.

## Completion notes

