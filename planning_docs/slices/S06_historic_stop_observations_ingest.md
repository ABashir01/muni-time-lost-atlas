# Title
S06 Historic Stop Observations Ingest

## Goal
Load a small historical `stop_observations` fixture from 511-style data and prove the project can parse observed arrivals.

## Why this slice exists
Observed stop arrivals are necessary for waiting-loss and scheduled-vs-observed runtime analysis.

## Depends on
- `S03_python_project_bootstrap`
- `S05_canonical_scheduled_models`

## Touches
- raw historical observation ingest code
- raw observation tables
- historical fixture files

## Inputs
- 511 historic feed assumptions from `03_data_sources.md`

## Outputs
- raw observed-stop data in the database
- typed timestamps and route/trip/stop fields where available

## Implementation notes
- keep scope narrow and fixture-driven
- do not solve every historical edge case in this slice
- assume the historic feed source is the regional `RG` path prepared by the prior fetch slice

## Tests required
- row-count assertions
- timestamp parsing validation
- basic not-null checks on required observation fields

## Acceptance criteria
- a deterministic observation fixture loads successfully
- the raw table is usable for scheduled/observed joining

## Non-goals
- canonical observed models
- join logic
- metrics

## Handoff to next slice
Next slice joins scheduled and observed stop events.

## Completion notes
