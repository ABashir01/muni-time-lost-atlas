# Title
S24 Route Detail With Fixtures

## Goal
Build the route detail page against static fixture data.

## Why this slice exists
The route detail page needs to prove its information hierarchy and terminology before live data is introduced.

## Depends on
- `S21_design_system_primitives`

## Touches
- route detail page
- summary and detail components
- route fixture data

## Inputs
- route summary contract
- product wording from `01_product_experience.md`

## Outputs
- fixture-driven route detail page

## Implementation notes
- prioritize metric wording and section order
- keep charts simple and deterministic

## Tests required
- route detail render test
- summary-section presence assertions

## Acceptance criteria
- route detail page explains total loss, waiting/travel split, where, and when

## Non-goals
- live API integration
- compare view

## Handoff to next slice
Next slice builds the compare view.

## Completion notes

