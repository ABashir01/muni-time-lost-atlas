# Title
S23 Map View With Fixtures

## Goal
Build the map page against static geometry and metric fixtures.

## Why this slice exists
Map behavior and UI structure should be validated before live endpoint integration.

## Depends on
- `S21_design_system_primitives`
- `S22_homepage_with_fixtures`

## Touches
- map page
- geometry fixtures
- selection/detail panel behavior

## Inputs
- map contract from `05_api_contract.md`
- spatial behavior from `01_product_experience.md`

## Outputs
- functioning fixture-based map page

## Implementation notes
- use map-ready fixture data
- keep live vehicle overlays out of this slice

## Tests required
- render test
- route selection interaction smoke test

## Acceptance criteria
- map page renders route layers and selection UI from fixtures

## Non-goals
- API integration
- GTFS-RT overlay

## Handoff to next slice
Next slice builds the route detail page.

## Completion notes

