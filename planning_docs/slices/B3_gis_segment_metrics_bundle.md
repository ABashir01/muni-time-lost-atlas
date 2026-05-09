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
- What changed:
  - added a small raw transit-lane overlay fixture + loader and staged it through dbt
  - materialized `canonical.route_geometries`, `canonical.stop_points`, and `canonical.route_stop_segments`
  - materialized `marts.route_segment_metrics` with an explicit `adjacent_stop_pair` strategy
  - materialized `serving.route_map_layer`, `serving.route_segment_layer`, `serving.stop_map_layer`, and `serving.transit_only_lane_overlay`
  - threaded `worst_segment_label` into route summary marts for later route-detail and map use
- Tests run:
  - `.\.venv\Scripts\python.exe -m unittest tests.integration.test_gis_segment_metrics_bundle tests.integration.test_core_metrics_bundle -v`
- What passed:
  - route geometry, segment metrics, stop points, and transit-lane overlay are queryable from PostGIS-backed dbt models
  - the controlled fixture produces stable adjacent-stop segment loss outputs and worst-segment labels
  - prior core route metric math remains unchanged on the regression path
- Known limitations / follow-up:
  - the first segment layer is in-vehicle only and does not allocate waiting loss onto segments
  - segment identity remains shape-specific; future branching/short-turn routes may need an additional route-pattern abstraction
  - the overlay is intentionally contextual and is not used in any inferential metric
