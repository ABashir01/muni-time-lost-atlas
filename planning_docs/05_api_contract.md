# API Contract

## Contract Principles
- frontend should consume stable, documented response shapes
- endpoints should serve precomputed summaries, not raw telemetry
- API changes must be reflected in this document in the same slice
- fixture JSON should mirror the planned response contract before live integration

Current historical summary sources after `B1`:
- `marts.route_window_summary`
- `marts.route_direction_summary`
- `marts.route_hour_summary`

Current spatial/segment sources after `B3`:
- `serving.route_map_layer`
- `serving.route_segment_layer`
- `serving.stop_map_layer`
- `serving.transit_only_lane_overlay`

Current stop-wait source after `B3a`:
- `serving.stop_wait_hotspots`

Current `B1` limitation:
- the only materialized route window is `all_day`
- unmatched observations are surfaced through summary count fields, not blended into metric values

## Planned Endpoints
- `GET /health`
- `GET /rankings?window=&metric=&mode=`
- `GET /routes/{route_id}/summary?window=&direction=`
- `GET /routes/{route_id}/segments?window=&direction=`
- `GET /routes/{route_id}/stops/wait?window=&direction=`
- `GET /routes/compare?ids=&window=`
- `GET /map/routes?window=&metric=`
- `GET /live/vehicles`

## Core Shared Fields
Most route-centric responses should use:
- `route_id`
- `route_name`
- `window`
- `direction` when applicable
- `typical_trip_loss_minutes`
- `waiting_loss_minutes`
- `in_vehicle_loss_minutes`
- `worst_time_band`
- `worst_stop_wait_label`
- `worst_segment_label`
- `metric_updated_at`

Current `B1` summary tables also expose diagnostic coverage fields:
- `matched_observed_stop_event_count`
- `resolved_unmatched_observation_count`
- `matched_headway_interval_count`
- `matched_full_trip_count`

## Rankings Response
Purpose:
- power homepage route ranking cards

Expected shape:
- selected `window`
- selected `metric`
- ordered list of route summaries

Each route summary should include:
- route identity fields
- total loss
- waiting/travel split
- worst time band
- worst stop wait label
- worst segment label

## Route Summary Response
Purpose:
- power route detail page header and summary section

Should include:
- total typical trip loss
- waiting loss
- in-vehicle loss
- bunching rate when available
- worst time band
- worst stop wait label
- worst segment label
- short interpretive label if generated server-side later

## Segment Response
Purpose:
- power route detail map panels and selected corridor summaries

Should include:
- route and direction
- segment identity or label
- adjacent stop-pair identity for the first bundle
- embedded segment geometry from PostGIS-serving tables
- segment-level in-vehicle loss metric for the first implementation

Current `B3` implementation notes:
- first segment strategy is `adjacent_stop_pair`
- labels use stop-to-stop rider language such as `16th St Mission -> 24th St Mission`
- `segment_in_vehicle_loss_minutes` is the first published segment metric; waiting loss is not allocated to segments in `B3`

Current `B3a` implementation notes:
- stop-based waiting burden is exposed as `serving.stop_wait_hotspots`
- `stop_wait_strategy` keeps the first-stop-only conservative scope explicit
- stop waiting remains separate from segment loss

## Stop Wait Hotspots Response
Purpose:
- power route-detail stop hotspot panels and future stop-wait map overlays

Should include:
- route and direction
- stop identity and label
- stop geometry from serving tables
- `stop_wait_strategy` so the first-stop-only scope remains explicit
- scheduled effective wait
- observed effective wait
- waiting loss
- matched headway interval count

## Map Response
Purpose:
- power citywide route choropleth / thematic map

Should include:
- route geometry or geometry reference
- route-level metric to color by
- route identity
- updated timestamp

Current `B3` implementation notes:
- route geometry is materialized in `serving.route_map_layer`
- stop geometry is materialized in `serving.stop_map_layer`
- transit-lane context is materialized in `serving.transit_only_lane_overlay`
- overlays remain contextual and should not be presented as causal proof

## Compare Response
Purpose:
- power 2-4 route compare view

Should include:
- shared selected time window
- one summary block per route
- same summary fields used in rankings/detail when possible

## Live Vehicles Response
Purpose:
- optional map overlay only

Should include:
- vehicle ID
- route ID
- route name or display token if needed
- latitude / longitude
- timestamp

This endpoint is deferred until static/historical data paths are correct.

## Fixture Rules
- every major endpoint should get fixture JSON before frontend live integration
- fixture names should clearly map to endpoints
- fixture data should be plausible and reflect documented field names exactly
