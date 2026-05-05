# Title
S32 Live Map Overlay

## Goal
Add the optional live vehicle overlay to the map view without changing the map’s primary meaning.

## Why this slice exists
Live data should enrich the map without displacing the product’s historical/static reliability story.

## Depends on
- `S28_map_integration`
- `S31_live_vehicle_endpoint`

## Touches
- map overlay rendering
- overlay controls
- live vehicle fetching

## Inputs
- live vehicle endpoint
- integrated map page

## Outputs
- optional live vehicle dots on the map

## Implementation notes
- keep overlay toggleable
- route-color choropleth remains the primary visual meaning

## Tests required
- overlay render smoke test
- overlay toggle behavior test

## Acceptance criteria
- live vehicles can be shown without confusing the route-loss map semantics

## Non-goals
- real-time analytics
- trip update explanations

## Handoff to next slice
Next slice finalizes the public methodology page.

## Completion notes

