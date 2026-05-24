# Title
B7 Rolling Historical Publication Bundle

## Goal
Turn the real cutover pipeline into a production-like rolling historical publication flow.

## Why this bundle exists
The current product can build one accepted real monthly cutover, but the MVP still needs a repeatable publishing pattern for the live app database.

This bundle exists to make the product:
- operate on a rolling historical window
- update on a monthly cadence
- avoid pretending to be a realtime system

## Depends on
- `B6_frontend_api_integration_bundle`
- `B6a_real_dataset_cutover_bundle`
- `B6b_real_map_engine_bundle`
- `B6c_historic_shapes_api_fallback`

## Touches
- monthly cutover orchestration
- retention-window policy
- app publication cadence
- deployment/run scheduling inputs

## Inputs
- active `511` operator GTFS
- historic monthly `RG -so` archives
- Shapes API fallback when recent monthly archives omit `shapes.txt`
- existing historical/static API and frontend

## Outputs
- rolling historical publication in the live app DB
- documented retention window
- repeatable monthly refresh flow
- date-range support across the retained window

## Implementation notes
- use a **rolling 6-month** live database window
- update the published dataset on a **monthly** cadence when the next `RG -so` archive is available
- keep the product historical/static in methodology and behavior
- do not add GTFS-RT vehicle overlays in this bundle
- do not add live endpoint semantics in this bundle
- make date filtering/range selection operate over the retained historical window, not over fake presets that imply realtime freshness
- keep older monthly archives outside the live serving window as retained artifacts or backups rather than in the app DB
- use the existing real cutover path as the publication mechanism
- use the accepted historic Shapes API fallback during the build when recent monthly archives omit `shapes.txt`

### Source cadence assumption
`511` historic `RG -so` publication should be treated as a **last-completed-month** source, not a current-month source.

Current verification snapshot:
- on `2026-05-24`, `historic=2026-05-so` returned `404`
- on `2026-05-24`, `historic=2026-04-so` returned `200`

Operational implication:
- the app should publish the newest **completed** month once `511` exposes it
- the app should not wait for same-month or same-day historical availability

### Cron strategy
Recommended production behavior:
- run a lightweight availability check **daily**
- target the newest completed month, not the current month
- when the next month becomes available, run the full rolling-window publication cutover once
- skip republishing when the month is still unavailable or unchanged

Recommended initial cron window:
- start checking on the **2nd day of each month**
- continue daily until the newest completed month is available and published
- after successful publication, remain idle until the next monthly cycle

This is preferable to a fixed once-per-month fire-and-forget job because:
- `511` documents the historic feed as monthly and retrospective
- but does not promise a precise day-of-month publication timestamp in the public docs
- the daily availability check keeps the app current without requiring manual intervention

## Tests required
- one primary integration suite for rolling-window cutover and retention behavior
- one regression suite for API/frontend compatibility against the refreshed monthly publication window
- live `511` verification only for the monthly cutover inputs, not for realtime polling

## Acceptance criteria
- the live app DB can be rebuilt/published from the most recent supported monthly archive
- the published window retains the last 6 months and drops older live-serving months from the primary app DB
- homepage, rankings, compare, route detail, and map still work against the rolling historical window
- methodology and copy remain consistent with a monthly-refreshed historical product
- no part of the app implies second-by-second or same-day live metric freshness
- the publication job can detect that the newest completed month is not yet available and exit cleanly without mutating the live DB

## Non-goals
- GTFS-RT vehicle positions
- live map overlays
- same-day metric recomputation
- major API redesign
- replacing Postgres/PostGIS with a warehouse or file-based serving store

## Handoff to next bundle
`B8_product_hardening_bundle` should polish the full product and finalize public-facing behavior.

## Completion notes
