# Data Model

## Schema Strategy
Use five Postgres schemas:
- `raw`
- `staging`
- `canonical`
- `marts`
- `serving`

This naming is now locked for MVP planning purposes.

This layered model should be understood as closest to `dbt`-style `staging` / `intermediate` / `marts` guidance:
- `raw` preserves landed source data outside the transformation graph
- `staging` cleans and normalizes source-specific structure
- `canonical` plays the role of stable reusable intermediate entities
- `marts` contains product-facing aggregates
- `serving` contains API-facing helpers and live-serving tables/views

`medallion` is a useful conceptual analogy only. Do not rename schemas to `bronze`, `silver`, or `gold`.

Rules:
- `raw` preserves source-file structure and source field names as much as practical.
- `staging` normalizes types and local time handling but stays close to source entities.
- `canonical` exposes the stable scheduled and observed entities that downstream metrics should depend on.
- `marts` contains aggregate metric tables built for rankings, compare views, and map summaries.
- `serving` is reserved for API-ready helper views/tables and later realtime-serving entities.

`S04` should create only `raw` GTFS tables.
`S05` should transform from `raw` and `staging` into the first `canonical` scheduled tables.

## Raw Layer
### Raw source groups
- GTFS static snapshots
- historic stop observations
- GTFS-RT vehicle snapshots later
- GIS overlays later

### Raw layer goals
- preserve source fidelity
- type minimally
- capture ingest metadata needed to identify fixture loads and later feed snapshots

### Raw provenance guidance
The raw layer must preserve enough provenance to distinguish:
- active `511` operator-specific feeds used for scheduled baseline work
- historic `511` regional feeds used for archived GTFS plus `stop_observations`
- later GTFS-RT polling snapshots

At minimum, raw entities should carry implementation support metadata for:
- source system, e.g. `511`
- feed scope, e.g. `operator_active`, `regional_historic`, `gtfs_rt`
- operator identifier where applicable, e.g. `SF`
- snapshot or batch label, e.g. feed date or historic month
- `ingested_at`

This metadata should supplement source identifiers, not replace them.

### Initial raw GTFS table list for `S04`
The first ingest slice should create and load only these GTFS tables:
- `raw.gtfs_routes`
- `raw.gtfs_trips`
- `raw.gtfs_stops`
- `raw.gtfs_stop_times`
- `raw.gtfs_shapes`
- `raw.gtfs_calendar`
- `raw.gtfs_calendar_dates`

These are the minimum scheduled entities needed to support:
- route/trip/stop parsing
- stop-event construction
- service-date expansion in `S05`
- shape linkage for later GIS work without requiring geometry modeling yet

### Raw naming rules
- use `gtfs_` table prefixes in `raw` for static GTFS source files
- keep standard GTFS business-key column names unchanged where possible:
  - `route_id`
  - `trip_id`
  - `stop_id`
  - `service_id`
  - `shape_id`
- keep source GTFS field names unchanged in raw, including `arrival_time` and `departure_time`
- add ingest metadata columns only as implementation support, not as replacements for GTFS identifiers

### Deferred raw observed and realtime entities
Future slices should use these names unless a later decision explicitly changes them:
- `raw.stop_observations`
- `raw.gtfs_rt_vehicle_positions`

`S06` should land historic observed arrivals in `raw.stop_observations`.
`S30` should land GTFS-RT vehicle snapshots in `raw.gtfs_rt_vehicle_positions`.

### Initial raw stop observations fields for `S06`
The first historical observation ingest slice should preserve these source-facing fields in `raw.stop_observations`:
- `service_date`
- `trip_id`
- `stop_id`
- `stop_sequence`
- `observed_arrival_time`

`S06` may also derive a typed `observed_arrival_ts` alongside the source timestamp text so later slices can validate and compare observed arrival times without reparsing the raw text value repeatedly.

For the real historic `RG` archive path:
- map source `to_stop_id` into raw `stop_id`
- parse compact `service_date` values such as `20230214` into the raw `service_date` date column
- derive `observed_arrival_ts` from service-day clock times such as `25:15:00` in local Bay Area time
- keep snapshot labeling explicit enough to distinguish fixture loads from real archive-backed loads

## Staging Layer
### Staging goals
- normalize column names only where source quirks would leak into downstream models
- parse service-date and time fields into stable typed columns
- isolate GTFS local-time edge cases from canonical models
- reconcile active-operator and historic-regional feed differences before canonical models depend on them

### First staged entity families
- `staging.gtfs_routes`
- `staging.gtfs_trips`
- `staging.gtfs_stops`
- `staging.gtfs_stop_times`
- `staging.gtfs_shapes`
- `staging.gtfs_service_dates`

`staging.gtfs_service_dates` should be the first place where `calendar` and `calendar_dates` are reconciled into explicit service dates.

Future staged entity families should include:
- `staging.stop_observations`
- `staging.gtfs_rt_vehicle_positions`

The staging layer is where later slices should reconcile:
- active operator feed IDs versus historic regional feed IDs/namespacing
- differing historic feed calendar/date representations
- source-specific time and timestamp quirks
- raw feed provenance into stable downstream join inputs

## Canonical Layer
### Canonical goals
- define stable scheduled entities that metrics and APIs can depend on
- separate scheduled models from observed models explicitly
- avoid exposing raw GTFS quirks to downstream slices

### Initial canonical scheduled table list for `S05`
`S05` should create these first canonical scheduled tables:
- `canonical.scheduled_routes`
- `canonical.scheduled_trips`
- `canonical.scheduled_stops`
- `canonical.service_dates`
- `canonical.scheduled_stop_events`

These tables are enough for the next slices to rely on a stable scheduled baseline without touching `raw` GTFS tables directly.

### Canonical scheduled table intent
- `canonical.scheduled_routes`
  - one row per published route in the active GTFS fixture
- `canonical.scheduled_trips`
  - one row per scheduled trip with stable linkage to route, service, direction, and shape
- `canonical.scheduled_stops`
  - one row per stop with stable stop metadata and location fields
- `canonical.service_dates`
  - explicit service-date expansion for each `service_id`
- `canonical.scheduled_stop_events`
  - one row per scheduled stop event for a specific `trip_id`, `stop_sequence`, and `service_date`

Deferred but reserved canonical entity names:
- `canonical.observed_stop_events`
- `canonical.route_geometries`
- `canonical.stop_points`

`S07` should target `canonical.observed_stop_events` as the first stable observed-event interface after raw/staged observation ingest.

### Initial canonical observed entity intent for `S07`
- `canonical.observed_stop_events`
  - exact-match scheduled/observed stop events only
  - conservative join on `service_date`, `trip_id`, `stop_sequence`, and `stop_id`
  - exposes both scheduled and observed timestamps for later waiting/runtime calculations
- `canonical.observed_stop_event_join_audit`
  - one row per raw observed stop event with explicit join status
  - surfaces unmatched or mismatch cases instead of hiding them with heuristics
- `canonical.observed_stop_event_join_summary`
  - grouped counts by observed snapshot and join status for quick validation

## Naming Conventions
### Keys
- use GTFS business identifiers directly as the canonical business keys for early slices:
  - `route_id`
  - `trip_id`
  - `stop_id`
  - `service_id`
  - `shape_id`
- do not rename GTFS identifiers to app-specific names in `raw`, `staging`, or the first canonical scheduled tables
- if a later slice needs warehouse-style surrogate keys, add them in addition to these business keys rather than replacing them

### Service dates
- use `service_date` as the standard date column name
- `service_date` should be typed as a calendar date in local agency service terms, not as a UTC timestamp
- `canonical.service_dates` is the source-of-truth table for expanded active dates per `service_id`

### Time and timestamp fields
- raw GTFS tables should preserve original source field names such as `arrival_time` and `departure_time`
- use `_time_text` only in normalized layers where a renamed source-clock field is intentionally retained
- use `_secs` for service-day-relative seconds from local midnight, especially for GTFS times that can exceed `24:00:00`
- use `_ts` for derived wall-clock timestamps when they are needed
- for scheduled GTFS modeling, treat local service-day time as primary; do not make UTC conversion the canonical representation in early slices

Examples:
- `arrival_time_text`
- `departure_time_text`
- `arrival_time_secs`
- `departure_time_secs`
- `scheduled_arrival_ts`
- `scheduled_departure_ts`

### Geometry columns
- use `geom` as the standard geometry column name
- point tables should use `geom` with point geometry
- line tables should use `geom` with line geometry
- keep source latitude/longitude columns alongside `geom` where the source provides them

Geometry-bearing canonical tables are later work, but this naming should be used once geometry modeling begins.

## Marts
Expected marts:
- route-hour metrics
- route-day metrics
- route-direction metrics
- route-segment metrics
- compare-ready summary marts

The first mart should support a route ranking query for one time window.

### First `B1` mart tables
`B1` materializes these first summary tables:
- `marts.route_window_summary`
- `marts.route_direction_summary`
- `marts.route_hour_summary`

Current scope rules:
- metrics are built from `canonical.observed_stop_events` matched rows only
- unmatched rows from `canonical.observed_stop_event_join_audit` are kept out of the metric numerators
- route-level summaries expose separate coverage counts for matched rows and route-resolved unmatched rows
- the only materialized route window in `B1` is `all_day`

Key metric fields in these marts:
- `typical_trip_loss_minutes`
- `waiting_loss_minutes`
- `in_vehicle_loss_minutes`

Key diagnostic fields in these marts:
- `matched_observed_stop_event_count`
- `resolved_unmatched_observation_count`
- `matched_headway_interval_count`
- `matched_full_trip_count`

## Serving Layer
Expected serving entities later:
- API-ready route summary views or tables
- API-ready map summary views
- `serving.current_vehicle_positions`
- optional `serving.route_map_summaries`

This schema is later-phase and should remain separate from historical metric marts.

`S31` should expose live vehicle data from a small serving-friendly current-state representation rather than directly from raw GTFS-RT snapshots.

## Update Rhythm And Retention
The schema strategy should reflect two different operational rhythms:

- historical/static GTFS and archived `stop_observations`
  - ingested in batch by fixture, feed date, or historic month
  - normalized into canonical entities
  - aggregated into marts on a slower refresh cadence

- realtime GTFS-RT vehicle polling
  - ingested on a modest recurring cadence
  - stored in raw form only as long as needed for current-state and short-horizon debugging
  - surfaced through a compact serving-layer current-state interface

Do not treat realtime snapshots as the primary long-term analytical store. Long-horizon product queries should come from canonical historical entities and marts.

## Key Modeling Concerns
- route and trip key stability across feeds
- active operator versus historic regional feed reconciliation
- GTFS service-date expansion from `calendar` plus `calendar_dates`
- times past `24:00:00`
- short turns
- direction grouping
- scheduled-to-observed join logic
- segment identity choice
- spatial validity for route/stop geometry
