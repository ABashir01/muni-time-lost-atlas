# Title
B6c Historic Shapes API Fallback

## Goal
Enable recent historic monthly cutovers even when 511's `RG -so` archive omits
`shapes.txt`, while preserving map functionality, build reproducibility, and a
clear truth model.

## Why this bundle exists
Recent monthly historic archives appear to remain valid for schedule and
`stop_observations` data but may be missing `shapes.txt`. Without a fallback,
recent historical metric builds can succeed analytically while still failing to
produce route geometry for the map layers.

## Depends on
- `B6a_real_dataset_cutover_bundle`
- `B6b_real_map_engine_bundle` only insofar as the map-serving product already
  depends on route geometry

## Trigger condition
Run the fallback only when:
- the fetched historic archive is otherwise valid for the cutover
- but `shapes.txt` is missing from the source archive or the derived SF-only
  archive

Do not invoke the fallback when:
- `shapes.txt` is already present and non-empty

## Build-step insertion point
The fallback belongs in the cutover/build pipeline, not in the API or frontend:
- after the historic archive is fetched
- after SF-only filtering determines the retained `route_ids`, `trip_ids`, and
  route-direction-headsign geometry groups
- before GTFS archive ingest loads the derived archive into `raw.gtfs_*`

## Fallback strategy
Use:
- one stable geometry target per retained historic trip when source `shape_id` is missing,
  then collapse those targets only when an exact current-geometry match is defensible

Rules:
- read `trips.txt` from the filtered historic archive
- when source `shape_id` values are missing, synthesize a stable placeholder geometry target
  in the derived `trips.txt`
- first satisfy the target from the already-fetched current active GTFS archive when:
  - the normalized historic trip id still exists as a current active trip id, or
  - the exact `route_id + direction_id + trip_headsign + stop pattern` match converges on
    one unique active `shape_id`
- if active GTFS rows cannot satisfy the target directly, try Shapes API candidates in a
  reduced order:
  - normalized historic trip id first
  - exact current stop-pattern candidate trips next
  - same `route_id + direction_id + trip_headsign` current trips only as the last
    Shapes API fallback when exact-pattern candidates do not exist
- parse the returned `LineString.pos[]` coordinates into GTFS-style
  `shapes.txt` rows
- synthesize a `shapes.txt` file inside the derived archive before ingest

Do not use:
- one request per `trip_id`
- one request per route-direction
- runtime/live frontend or API fetches of shape geometry

## Output contract
The fallback should produce:
- a complete `shapes.txt` in the derived archive when the build succeeds
- provenance metadata that explicitly records:
  - source archive lacked `shapes.txt`
  - whether exact active trip-id/current stop-pattern geometry reuse was sufficient
  - whether Shapes API fallback was used
  - count of missing geometry targets
  - count of successful shape backfills
  - count of Shapes API requests made
  - trip-selection strategy
  - Shapes API cache-hit count

## Truth model
This fallback uses current Shapes API geometry.

That means:
- metrics remain historical for the selected month or date range
- geometry is a display fallback used when the historic monthly archive is
  incomplete
- the resulting map is acceptable for recent rolling-history publication
- the resulting map is not guaranteed to be month-perfect historical geometry
- when historic stop-distance values extend beyond the current geometry length,
  downstream segment publication may need to fall back to straight stop-to-stop
  lines instead of route substrings

## Failure policy
If any required `shape_id` cannot be backfilled:
- fail the build
- do not publish a partial cutover by default

Reason:
- this keeps map integrity stronger
- it preserves provenance discipline
- it avoids silently dropping route geometry from the public product

## Caching and provenance expectations
The implementation should:
- cache Shapes API responses or synthesized shape outputs under `artifacts/`
- record enough metadata to make the build reproducible
- avoid repeated refetching for unchanged shape backfills during reruns when
  cached outputs are still valid

## Important interface and data-contract changes
This is a markdown-only design pass, but the intended future contract additions
are:
- the historic cutover pipeline gains a geometry-enrichment phase
- the derived SF-only historic archive may contain:
  - original `shapes.txt`, or
  - synthesized `shapes.txt` built from current active-GTFS geometry reuse and,
    only when necessary, Shapes API responses
- cutover manifests should eventually record:
  - `shape_fallback_used`
  - `shape_backfill_request_count`
  - `shape_backfill_shape_count`
  - `shape_backfill_failure_count`

## Tests required
- archive has `shapes.txt`
  - fallback does not run
  - original archive geometry is preserved
- archive lacks `shapes.txt`
  - fallback runs
  - current active-GTFS shape rows are reused first when either an exact current trip-id
    match exists or an exact `route_id + direction_id + trip_headsign + stop pattern`
    match converges on one unique active `shape_id`
  - Shapes API is only called when current active-GTFS rows cannot satisfy the
    geometry target
  - synthesized `shapes.txt` is present before ingest
- source trips with blank `shape_id`
  - stable placeholder geometry targets are synthesized in the derived archive
- ambiguous active matches
  - direct active-archive geometry reuse is skipped
  - the build falls through to Shapes API candidates or fails
- at least one required `shape_id` cannot be fetched
  - cutover fails
  - manifest/log identifies the unresolved geometry target
- recent historic cutover with fallback enabled still produces:
  - route geometries
  - route map layer
  - segment layers
  - normal frontend map compatibility

## Non-goals
- proving that Shapes API geometry is historically exact for the selected month
- adding runtime shape fetches to the public app
- changing the metric math itself

## Handoff to next bundle
`B7` should assume this fallback exists if recent rolling historical publication
depends on monthly archives that may be missing `shapes.txt`.
