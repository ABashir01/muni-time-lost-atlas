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

Current `B4` scope limits:
- `window=all_day` is the only supported historical/static API window
- `/rankings` currently supports only `mode=routes`
- stop-wait hotspot data remains limited to the conservative first-stop exact-match methodology

Current public-unit limitation:
- the public homepage rankings and current citywide map contract are route-level
  rather than direction-level
- `marts.route_direction_summary` already exists beneath this layer, but the
  public ranking/map contract does not yet use it
- a future deferred API evolution should add direction-level public ranking and
  map support instead of continuing to pool materially different directions into
  one published route entry

## Implemented Endpoints
- `GET /health`
- `GET /rankings?window=all_day&metric={typical_trip_loss_minutes|waiting_loss_minutes|in_vehicle_loss_minutes}&mode=routes`
- `GET /routes/{route_id}/summary?window=all_day&direction={0|1 optional}`
- `GET /routes/{route_id}/segments?window=all_day&direction={0|1 required}`
- `GET /routes/{route_id}/stops/wait?window=all_day&direction={0|1 required}`
- `GET /routes/compare?ids=14,49&window=all_day`
- `GET /map/routes?window=all_day&metric={typical_trip_loss_minutes|waiting_loss_minutes|in_vehicle_loss_minutes}`

Deferred endpoints:
- `GET /live/vehicles`

## Core Shared Fields
Most route-centric responses should use:
- `route_id`
- `route_name`
- `route_short_name`
- `route_long_name`
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

Current implementation note:
- rankings currently publish route-level entries only
- the deferred future public contract should add a direction-aware mode where
  the ranking unit becomes `route_id + direction_id`

Shape:
- top-level `window`
- top-level `metric`
- top-level `mode`
- ordered `routes` list

Each route summary should include:
- `rank`
- route identity fields
- total loss
- waiting/travel split
- worst time band
- worst stop wait label
- worst segment label
- metric coverage counts
- `metric_updated_at`

## Route Summary Response
Purpose:
- power route detail page header and summary section

Shape:
- a single route summary object
- `direction_id` and `direction_label` only when `direction` is requested

Includes:
- total typical trip loss
- waiting loss
- in-vehicle loss
- worst time band
- worst stop wait label
- worst segment label
- metric coverage counts
- `metric_updated_at`

## Segment Response
Purpose:
- power route detail map panels and selected corridor summaries

Shape:
- top-level route metadata
- top-level `window`
- top-level `direction_id`
- top-level `direction_label`
- top-level `type = FeatureCollection`
- `features[]`, each with GeoJSON `geometry` plus typed `properties`

Segment feature properties include:
- route identity fields
- `shape_id`
- `segment_strategy`
- `segment_sequence`
- `from_stop_id`
- `from_stop_name`
- `to_stop_id`
- `to_stop_name`
- `segment_label`
- `scheduled_segment_minutes`
- `segment_in_vehicle_loss_minutes`
- `matched_trip_segment_count`
- `metric_updated_at`

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

Shape:
- top-level route metadata
- top-level `window`
- top-level `direction_id`
- top-level `direction_label`
- top-level `type = FeatureCollection`
- `features[]`, each with GeoJSON `geometry` plus typed `properties`

Stop-wait feature properties include:
- route identity fields
- `stop_id`
- `stop_name`
- `stop_wait_label`
- `stop_wait_strategy`
- `scheduled_effective_wait_minutes`
- `observed_effective_wait_minutes`
- `waiting_loss_minutes`
- `matched_headway_interval_count`
- `metric_updated_at`

Current `B4a` implementation notes:
- the endpoint reads directly from `serving.stop_wait_hotspots`
- `direction` is required because stop-wait rows are direction-specific
- `stop_wait_strategy` keeps the first-stop-only conservative scope explicit
- route-level summaries and map payloads still surface `worst_stop_wait_label`

## Map Response
Purpose:
- power citywide route choropleth / thematic map

Current implementation note:
- the current map response publishes one route-level feature per route
- the deferred future contract should move the public map unit to
  route-direction-level so the citywide map stays consistent with future
  direction-level homepage and rankings behavior
- that future shift will require a deliberate cartographic strategy for
  overlapping inbound/outbound features

Shape:
- top-level `window`
- top-level `metric`
- top-level `type = FeatureCollection`
- `features[]`, each with route GeoJSON `geometry` and `properties`

Route map feature properties include:
- the shared route summary fields
- metric coverage counts
- selected `metric`
- selected `metric_value`

Current `B3` implementation notes:
- route geometry is materialized in `serving.route_map_layer`
- stop geometry is materialized in `serving.stop_map_layer`
- transit-lane context is materialized in `serving.transit_only_lane_overlay`
- overlays remain contextual and should not be presented as causal proof

## Compare Response
Purpose:
- power 2-4 route compare view

Deferred evolution note:
- compare is currently route-level
- the future direction-aware public contract should allow compare items to
  identify both route and direction rather than only `route_id`

Shape:
- top-level `window`
- top-level `route_ids` preserving requested order
- one route summary block per route

Rules:
- accepts 2-4 comma-separated route ids
- rejects duplicate route ids
- uses the same route summary fields as rankings/detail when possible

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

Current `B4` fixture set:
- `fixtures/api/health.json`
- `fixtures/api/rankings_all_day_typical_trip_loss_minutes_routes.json`
- `fixtures/api/route_14_summary_all_day.json`
- `fixtures/api/route_14_segments_direction_1_all_day.json`
- `fixtures/api/route_14_stops_wait_direction_1_all_day.json`
- `fixtures/api/routes_compare_14_49_all_day.json`
- `fixtures/api/map_routes_all_day_typical_trip_loss_minutes.json`

Static frontend clarification after `B5`:
- the accepted fixture set still publishes only one dedicated route-detail segment payload (`route_14_segments_direction_1_all_day.json`)
- frontend route pages for any additional published routes must therefore fall back to the shared summary/map fixtures until broader route-detail fixtures exist
