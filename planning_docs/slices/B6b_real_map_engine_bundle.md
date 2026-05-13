# Title
B6b Real Map Engine Bundle

## Goal
Replace the controlled schematic map surfaces with a real interactive map engine while preserving the accepted editorial hierarchy and design language.

## Why this bundle exists
The schematic map was useful for homepage visual lock and deterministic frontend review, but it is not the right long-term product surface for route geometry, overlays, and future live vehicles.

## Depends on
- `B6_frontend_api_integration_bundle`
- ideally `B6a_real_dataset_cutover_bundle`

## Recommended map engine
- `MapLibre GL JS`

## Touches
- frontend map components
- route detail map panel
- map page
- homepage map panel only as needed to preserve the accepted composition
- API only if additional geometry-serving endpoints are needed later

## Inputs
- accepted frontend hierarchy and design-system docs
- route/segment/stop-wait geometry already available from the current historical/static API and local overlay fixtures
- accepted live-API integration path from `B6`

## Outputs
- real map engine in the homepage map territory, route detail, and map page
- preserved editorial layout instead of a generic full-screen mapping app
- route geometry and contextual overlays rendered through the map engine

## Implementation notes
- preserve the accepted homepage composition; do not let the map engine replatform the entire homepage into a generic map-first dashboard
- start with route geometry and basic thematic styling
- keep transit-only lane overlay support
- prepare for later GTFS-RT live-vehicle overlays without implementing them yet
- prefer explicit map wrappers/components over ad hoc map setup embedded in page files
- if needed, keep the homepage map slightly less interactive than the full map page to preserve the editorial feel

## Tests required
- one frontend smoke pass covering homepage, route detail, and map page with the real map engine
- one focused browser check that the map library loads and route layers render without console/runtime failure

## Acceptance criteria
- the homepage still matches the accepted editorial hierarchy
- route detail and map page render real geometry through the map engine
- the migration does not regress the accepted API integration
- the app is structurally ready for later live vehicle overlays

## Non-goals
- realtime ingestion itself
- changing the ranking or metric methodology
- full geospatial backend redesign

## Handoff to next bundle
After `B6b`, proceed to `B7_realtime_bundle` so live vehicle overlays land on a real map surface instead of the schematic placeholder.
