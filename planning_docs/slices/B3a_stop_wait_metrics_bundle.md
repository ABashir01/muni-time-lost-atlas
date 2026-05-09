# Title
B3a Stop Wait Metrics Bundle

## Goal
Add stop-based waiting-loss metrics as a separate spatial layer.

## Why this bundle exists
Waiting loss is naturally a stop/boarding phenomenon, not a street-segment phenomenon. This bundle makes that distinction explicit instead of forcing waiting loss into the segment table.

## Depends on
- `B1_core_metrics_bundle`
- `B2_dbt_adoption_bundle`
- `B3_gis_segment_metrics_bundle`

## Touches
- dbt marts for stop-based waiting metrics
- dbt serving tables/views for stop wait hotspots
- route/detail/map-facing spatial metric outputs
- API contract docs for future stop metric exposure

## Inputs
- matched observed stop events
- scheduled stop events
- existing route/stop geometry outputs
- current waiting-loss methodology from `02_methodology.md`

## Outputs
- stop-based waiting metric table
- serving-ready stop wait hotspot layer
- explicit separation between stop waiting burden and segment in-vehicle burden

## Implementation notes
- compute waiting loss at the stop level, not by segment
- reuse the accepted headway-loss methodology, generalized beyond first-stop-only where supportable
- keep the first stop-wait strategy explicit and conservative
- do not force stop waiting loss into `route_segment_metrics`
- if needed, expose route-level worst-stop waiting labels separately from worst-segment labels

## Tests required
- one primary integration suite proving stop wait metrics are queryable with stop geometry
- one regression suite only if the route-level waiting summaries are materially changed

## Acceptance criteria
- stop-based waiting metrics exist and are queryable
- the project has an honest spatial representation of waiting burden separate from segment in-vehicle loss
- downstream API work can expose stop wait hotspots without ad hoc frontend math

## Non-goals
- replacing segment in-vehicle metrics
- causal claims about stop conditions
- realtime work

## Handoff to next bundle
`B4_api_bundle` should expose both route/segment summaries and, if included in scope, stop-based waiting hotspot outputs from stabilized serving tables.

## Completion notes
