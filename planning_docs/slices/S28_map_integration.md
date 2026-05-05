# Title
S28 Map Integration

## Goal
Replace map fixtures with live API-backed geometry and route-metric responses.

## Why this slice exists
The product’s GIS signal depends on serving real route geometry and route loss values.

## Depends on
- `S18_map_endpoints`
- `S23_map_view_with_fixtures`

## Touches
- map data fetching
- geometry layer wiring
- selection panel data flow

## Inputs
- map endpoint(s)
- fixture-based map page

## Outputs
- live map route rendering

## Implementation notes
- integrate route geometry first
- keep GTFS-RT live dots out until later

## Tests required
- map integration smoke test
- route selection with live data test

## Acceptance criteria
- map renders real route geometry and route loss values from the API

## Non-goals
- live vehicle overlay
- compare integration

## Handoff to next slice
Next slice integrates the compare page.

## Completion notes

