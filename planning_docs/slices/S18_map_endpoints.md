# Title
S18 Map Endpoints

## Goal
Expose route map geometry and route-level thematic metrics needed for the map view.

## Why this slice exists
The map should consume stable API shapes rather than reading directly from DB tables or custom one-off queries.

## Depends on
- `S12_geometry_ingest`
- `S17_route_summary_endpoint`

## Touches
- map endpoint(s)
- API contract doc
- integration tests

## Inputs
- route geometry
- route-level metric outputs

## Outputs
- `GET /map/routes`
- optional route segment endpoint if needed for map detail

## Implementation notes
- separate route-level map summary from live vehicles
- keep geometry strategy explicit and documented

## Tests required
- route geometry response test
- response schema assertions

## Acceptance criteria
- frontend map can render route layers from documented endpoint(s)

## Non-goals
- GTFS-RT live positions
- compare endpoint

## Handoff to next slice
Next slice adds compare support.

## Completion notes

