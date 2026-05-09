# Title
B7 Realtime Bundle

## Goal
Add live GTFS-RT vehicle context on top of the working historical/static MVP.

## Why this bundle exists
Realtime should be an enhancement layer added only after the historical/static product is already useful and trustworthy.

## Depends on
- `B6_frontend_api_integration_bundle`

## Touches
- GTFS-RT ingestion
- live vehicle serving endpoint
- frontend map overlay

## Inputs
- live `511` GTFS-RT vehicle positions
- existing historical/static map and route screens

## Outputs
- live vehicles on map
- optional live context without destabilizing the historical MVP

## Implementation notes
- ingest GTFS-RT vehicle positions from `511`
- add the live vehicle serving endpoint
- add a live map overlay in the frontend
- keep live context clearly secondary to the historical choropleth/summary logic
- do not recompute the full historical metrics layer on every realtime poll
- live data should update current-state tables only

## Tests required
- one primary integration suite for live ingest plus endpoint plus frontend overlay
- live `511` verification only because this bundle directly depends on live behavior

## Acceptance criteria
- vehicles appear on the map from the live endpoint
- the historical/static product still behaves correctly without live data
- realtime does not change the historical metric semantics

## Non-goals
- historical metric recomputation from live feeds
- major API redesign

## Handoff to next bundle
`B8_product_hardening_bundle` should polish the full product and finalize public-facing behavior.

## Completion notes
