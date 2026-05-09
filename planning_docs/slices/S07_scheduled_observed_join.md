# Title
S07 Scheduled Observed Join

## Goal
Create the first working join between scheduled stop events and observed stop events for a narrow, validated happy path.

## Why this slice exists
The metric math depends on matching observed service behavior back to scheduled entities.

## Depends on
- `S05_canonical_scheduled_models`
- `S06_historic_stop_observations_ingest`

## Touches
- canonical observed models
- scheduled/observed join logic
- transformation or dbt models

## Inputs
- canonical scheduled stop events
- raw observed stop arrivals

## Outputs
- joined observed stop-event model or view

## Implementation notes
- keep the first join conservative and documented
- prioritize explicit caveats over hidden heuristics

## Tests required
- fixture-level validation that expected scheduled and observed events join correctly
- mismatch counts or unmatched cases surfaced clearly

## Acceptance criteria
- at least one small fixture path proves scheduled and observed events can be connected
- the joined model is usable for waiting/runtime calculations

## Non-goals
- perfect systemwide join coverage
- route-level ranking marts
- API exposure

## Handoff to next slice
Next slice implements the waiting-time math on controlled inputs.

## Completion notes
- Changed files:
  - `db/sql/02-materialize-canonical-scheduled-models.sql`
  - `db/sql/04-materialize-canonical-observed-stop-events.sql`
  - `pipeline/src/muni_lta_pipeline/canonical_observed_stop_events.py`
  - `fixtures/stop_observations/regional_rg_join_validation/stop_observations.txt`
  - `tests/integration/test_scheduled_observed_join.py`
  - `README.md`
  - `pipeline/README.md`
  - `tests/README.md`
  - `planning_docs/06_data_model.md`
  - `planning_docs/09_decisions.md`
  - `planning_docs/slices/S07_scheduled_observed_join.md`
- What changed:
  - added a SQL-first `S07` materialization that creates:
    - `canonical.observed_stop_event_join_audit`
    - `canonical.observed_stop_event_join_summary`
    - `canonical.observed_stop_events`
  - kept the first join conservative by requiring exact matches on `service_date`, `trip_id`, `stop_sequence`, and `stop_id`
  - derived `scheduled_arrival_ts` and `scheduled_departure_ts` in the joined model so later waiting/runtime slices can compare scheduled and observed timestamps directly
  - surfaced mismatch states explicitly as `matched_exact`, `unmatched_trip_service_date`, `unmatched_stop_sequence`, `unmatched_stop_id`, and `duplicate_observation_key`
  - added a thin Python entrypoint for the new SQL materialization
  - added a join-validation fixture with both happy-path and explicit mismatch rows
  - updated the S05 scheduled materialization SQL to drop the new observed views before rematerializing scheduled tables so reruns stay idempotent
- Tests run:
  - `& '.\.venv\Scripts\python.exe' -m unittest tests.integration.test_scheduled_observed_join.ScheduledObservedJoinIntegrationTests tests.integration.test_scheduled_observed_join.ScheduledObservedJoinMismatchIntegrationTests -v`
  - `& '.\.venv\Scripts\python.exe' -m unittest tests.integration.test_scheduled_observed_join.ScheduledObservedJoinRealArchiveIntegrationTests -v`
- What passed:
  - the fixture-backed happy path joins all three expected stop events into `canonical.observed_stop_events`
  - the join exposes scheduled and observed timestamps plus `arrival_delay_secs` for downstream metric work
  - explicit mismatch rows are counted and labeled in the audit/summary views instead of being silently accepted
  - the optional live archive-backed path confirms bounded real `RG` observation rows surface as unmatched while historic scheduled-feed reconciliation is still out of scope
- Known limitations or follow-up issues:
  - this first join does not attempt historic feed reconciliation between active operator GTFS and historic regional `RG` schedules, so real archive rows currently remain unmatched by design
  - no heuristics are applied for near-miss stop IDs, trip remapping, or approximate time alignment; those are later-slice concerns
