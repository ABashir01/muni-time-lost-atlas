# Title
S29 Compare Integration

## Goal
Replace compare fixtures with live API-backed comparison data.

## Why this slice exists
The compare view should validate that the shared summary fields really work across multiple UI surfaces.

## Depends on
- `S19_compare_endpoint`
- `S25_compare_view_with_fixtures`

## Touches
- compare page data fetching
- input validation UX
- live comparison rendering

## Inputs
- compare endpoint
- fixture compare page

## Outputs
- live compare page

## Implementation notes
- keep field names aligned with shared summary contracts
- preserve readable loading/error states

## Tests required
- compare integration test
- invalid input-state test

## Acceptance criteria
- compare page renders live API data for 2-4 routes cleanly

## Non-goals
- GTFS-RT
- methodology copy polish

## Handoff to next slice
Next slice starts realtime GTFS-RT ingest.

## Completion notes

