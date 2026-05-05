# API Contract

## Contract Principles
- frontend should consume stable, documented response shapes
- endpoints should serve precomputed summaries, not raw telemetry
- API changes must be reflected in this document in the same slice
- fixture JSON should mirror the planned response contract before live integration

## Planned Endpoints
- `GET /health`
- `GET /rankings?window=&metric=&mode=`
- `GET /routes/{route_id}/summary?window=&direction=`
- `GET /routes/{route_id}/segments?window=&direction=`
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
- `worst_segment_label`
- `metric_updated_at`

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
- worst segment label
- short interpretive label if generated server-side later

## Segment Response
Purpose:
- power route detail map panels and selected corridor summaries

Should include:
- route and direction
- segment identity or label
- geometry reference or embedded geometry strategy to be decided during implementation
- segment-level travel or total loss metric

## Map Response
Purpose:
- power citywide route choropleth / thematic map

Should include:
- route geometry or geometry reference
- route-level metric to color by
- route identity
- updated timestamp

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

