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
- explicit future naming for observed stop-event and live-serving entity families
- concise provenance and update-rhythm guidance for historical versus realtime data

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
- `S06` and `S07` have explicit future names for observed-stop entities without forcing premature join design
- `S30` and `S31` have explicit future names for raw GTFS-RT snapshots and serving-layer current vehicle state
- no major namespace or naming-convention decision is left to the implementer

## Non-goals
- full final mart design
- segment schema perfection
- realtime schema design
- production migration implementation

## Handoff to next slice
`S04_gtfs_static_fixture_ingest` should use the chosen raw schema strategy, and `S05_canonical_scheduled_models` should use the chosen canonical model names and conventions.

## Completion notes
- Changed files:
  - `planning_docs/06_data_model.md`
  - `planning_docs/09_decisions.md`
  - `planning_docs/slices/S03a_schema_strategy.md`
- What changed:
  - locked the Postgres schema namespaces to `raw`, `staging`, `canonical`, `marts`, and `serving`
  - clarified that the layered model is closest to `dbt`-style `staging` / reusable-intermediate / `marts` guidance, with medallion retained only as a conceptual analogy
  - defined the minimum raw GTFS table list for `S04`
  - defined the first canonical scheduled table list for `S05`
  - documented naming conventions for GTFS business keys, `service_date`, service-day-relative time fields, derived timestamps, and geometry columns
  - clarified that `calendar` plus `calendar_dates` reconcile into service dates in `staging`, and that `canonical.service_dates` plus `canonical.scheduled_stop_events` are the first stable scheduled interfaces
  - added raw feed provenance guidance so later slices can distinguish 511 active operator feeds from historic regional feeds before reconciliation
  - reserved explicit future names for `raw.stop_observations`, `staging.stop_observations`, `canonical.observed_stop_events`, `raw.gtfs_rt_vehicle_positions`, `staging.gtfs_rt_vehicle_positions`, and `serving.current_vehicle_positions`
  - added a concise retention/update-rhythm note separating batch historical refreshes from bounded-retention realtime polling
  - recorded the schema-strategy decision in `09_decisions.md`
- Tests run:
  - manual doc review of `planning_docs/06_data_model.md`
  - manual cross-check against `planning_docs/slices/S04_gtfs_static_fixture_ingest.md`
  - manual cross-check against `planning_docs/slices/S05_canonical_scheduled_models.md`
  - manual cross-check against `planning_docs/slices/S06_historic_stop_observations_ingest.md`
  - manual cross-check against `planning_docs/slices/S07_scheduled_observed_join.md`
  - manual cross-check against `planning_docs/slices/S30_gtfs_rt_ingest.md`
  - manual cross-check against `planning_docs/slices/S31_live_vehicle_endpoint.md`
- Results:
  - `06_data_model.md` now names the schema layers explicitly and lists the first expected entities for `S04` and `S05`
  - `S04` can proceed without inventing raw namespaces or GTFS table names
  - `S05` can proceed without inventing canonical scheduled table names or time/key conventions
  - `S06` and `S07` now have explicit observed-entity naming and clearer feed-provenance guidance without locking the join implementation too early
  - `S30` and `S31` now have explicit raw and serving-layer realtime entity naming plus a storage/retention boundary
- Follow-up issues:
  - surrogate-key strategy is intentionally deferred until a later slice proves it is needed
  - segment-identity strategy remains deferred until later GIS/metric slices
