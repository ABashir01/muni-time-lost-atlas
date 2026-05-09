# Title
B3 GIS And Segment Metrics Bundle

## Goal
Add the first map-serving geometry and segment/corridor metric layer.

## Why this bundle exists
The product needs a real spatial story, not just route totals. This bundle creates the geometry and segment outputs needed by the map and route detail screens.

## Depends on
- `B2_dbt_adoption_bundle`

## Touches
- PostGIS-serving tables
- route and stop geometry outputs
- segment-level metric tables
- transit-lane overlay data

## Inputs
- stabilized marts and canonical models
- route and stop data already present in Postgres
- spatial/context overlays used for the public product

## Outputs
- route geometry layer
- segment metric layer
- transit-lane overlay layer

## Implementation notes
- ingest or materialize route geometry and stop geometry into PostGIS-serving tables
- load transit-lane overlay as contextual GIS data
- define one narrow segment strategy:
  - adjacent stop-pair or route-segment representation
- align segment labels with the product’s “where time is lost” language
- do not try to prove causal effect of transit-only lanes
- overlays are contextual, not inferential

## Tests required
- one primary integration suite proving route geometry and segment metrics are queryable together
- no separate live test unless the bundle directly depends on live external data

## Acceptance criteria
- map-serving geometry exists
- segment metric outputs exist and are consumable by route-detail/map screens
- overlay data can be joined or served without ad hoc frontend computation

## Non-goals
- API handlers
- frontend pages
- causal claims about overlays

## Handoff to next bundle
`B4_api_bundle` should expose route, segment, compare, and map outputs from these stabilized tables.

## Completion notes
