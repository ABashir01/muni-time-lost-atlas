# Title
S27 Route Detail Integration

## Goal
Replace route detail fixtures with live API-backed data.

## Why this slice exists
The route detail page is the most important explanatory page after the homepage.

## Depends on
- `S17_route_summary_endpoint`
- `S24_route_detail_with_fixtures`

## Touches
- route detail data fetching
- route ID handling
- loading/error states

## Inputs
- route summary endpoint
- route detail fixture page

## Outputs
- live route detail page

## Implementation notes
- keep page layout stable while swapping the source
- ensure empty/invalid route states are readable

## Tests required
- route detail fetch/render integration test
- invalid route handling test

## Acceptance criteria
- route detail page renders correctly from the live summary endpoint

## Non-goals
- map data integration
- compare integration

## Handoff to next slice
Next slice integrates map data.

## Completion notes

