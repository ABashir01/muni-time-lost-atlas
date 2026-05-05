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

