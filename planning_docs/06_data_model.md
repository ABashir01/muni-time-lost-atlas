# Data Model

## Modeling Layers
Use these layers:
- `raw`
- `staging`
- `canonical`
- `marts`
- `live-serving`

## Raw Layer
Raw source groups:
- GTFS static snapshots
- historic stop observations
- GTFS-RT vehicle snapshots later
- GIS overlays

Raw layer goals:
- preserve source fidelity
- type minimally
- capture ingest metadata

## Staging Layer
Staging goals:
- parse timestamps and service dates
- normalize identifiers and column names
- isolate source quirks from canonical models

Expected staged entities:
- routes
- trips
- stops
- stop_times
- shapes
- stop_observations
- overlay geometries

## Canonical Layer
Canonical goals:
- stable entities that downstream marts can depend on
- explicit scheduled vs observed separation

Expected canonical entities:
- `scheduled_stop_events`
- `observed_stop_events`
- `route_service_instances`
- `route_geometries`
- `stop_points`

## Marts
Expected marts:
- route-hour metrics
- route-day metrics
- route-direction metrics
- route-segment metrics
- compare-ready summary marts

The first mart should support a route ranking query for one time window.

## Live-Serving Layer
Expected live-serving entities:
- current vehicle positions or a serving view
- lightweight map-ready route layer if needed

This layer is later-phase and should remain separate from historical metric marts.

## Key Modeling Concerns
- route and trip key stability across feeds
- short turns
- direction grouping
- scheduled-to-observed join logic
- segment identity choice
- spatial validity for route/stop geometry

