# Title
S25 Compare View With Fixtures

## Goal
Build the compare page against static route comparison fixtures.

## Why this slice exists
The compare surface should be validated for clarity and layout before live data is introduced.

## Depends on
- `S21_design_system_primitives`
- `S24_route_detail_with_fixtures`

## Touches
- compare page
- comparison components
- compare fixture data

## Inputs
- compare contract from `05_api_contract.md`

## Outputs
- fixture-driven compare page

## Implementation notes
- cap fixture examples to 2-4 routes
- keep comparisons literal and readable

## Tests required
- compare page render test
- route-count behavior test

## Acceptance criteria
- compare page can express the intended 2-4 route comparison clearly

## Non-goals
- live integration
- GTFS-RT

## Handoff to next slice
Next slice wires homepage rankings to the API.

## Completion notes

