# Title
P3a Real Date-Range Architecture Sketch

## Purpose
Describe a concrete post-MVP architecture for **real historical date-range
exploration** across the public site.

This document is intentionally deeper than `P3_public_date_range_support.md`.
`P3` describes the product goal and cross-surface scope. This companion doc
describes how the feature should actually work in:
- frontend state and navigation
- API contracts
- pipeline/dbt
- production storage
- deployment/publication flow

## Product Model
The date-range feature should behave like **one shared public state**, not like
separate widget-level filters sprinkled across the site.

### Shared range behavior
- one date-range selector should live in the top shell area and appear
  consistently on:
  - homepage
  - rankings
  - map
  - route detail
  - compare
- changing the range on any page should update the same shared value
- navigating between pages should preserve the active range
- deep links should reopen the same range
- pages should not invent their own independent range state

### First-class product rule
The selected range is part of the user-visible product state in the same way
that:
- a selected route is state
- a selected compare pair is state
- a route direction will eventually be state

That means the range should be:
- shareable
- bookmarkable
- preserved through in-app navigation

## Frontend Design
### Selector placement
The selector should live high in the page shell, not buried inside one page.

Preferred placement:
- inside the shared masthead/header region
- below the main title row or aligned with the page navigation row
- visually consistent across all major product surfaces

This keeps the range feeling like:
- one editorial framing control for the product
and not:
- a page-local dashboard filter

### Selector behavior
Support:
- a few presets
- a custom start/end picker

Recommended presets:
- `Last 30 days`
- `Last 90 days`
- `Full live window`

Initial product rules:
- all selected dates must stay inside the retained live window
- if the user selects a preset, the frontend should resolve it to explicit
  `date_from` / `date_to` values before making API requests
- the custom range picker should reject invalid ranges before request dispatch

### URL/state contract
Use explicit query params:
- `date_from=YYYY-MM-DD`
- `date_to=YYYY-MM-DD`

Examples:
- `/`
  - defaults to the product default range
- `/rankings?date_from=2026-02-01&date_to=2026-04-30`
- `/map?date_from=2026-03-01&date_to=2026-03-31`
- `/routes/14?date_from=2026-02-15&date_to=2026-04-15`
- `/compare?ids=14,49&date_from=2026-02-01&date_to=2026-04-30`

### Frontend data flow
Recommended frontend shape:
1. read `date_from` / `date_to` from URL
2. normalize into one shared `DateRangeState`
3. pass that state into page-level data requests
4. when changed, update the URL rather than keeping hidden ephemeral state

This keeps:
- SSR coherent
- deep links reproducible
- page transitions consistent

### Frontend pages affected
#### Homepage
- hero copy should reflect the selected range
- hero rankings should use the selected range
- hero map highlight should use the selected range

#### Rankings page
- ordering should use the selected range
- header summary should say what range is being shown

#### Map page
- map color scale / ranking context should use the selected range
- any sidebar list should use the selected range

#### Route detail
- headline metrics should use the selected range
- directional details, segment layers, and stop-wait layers should use the
  selected range where available

#### Compare
- compare should use the same shared range
- compare route selections and the range should both survive navigation and
  deep linking

## API Design
### General rule
Do **not** compute public date ranges from raw stop observations at request
time.

Instead:
- compute daily facts in the pipeline
- aggregate those daily facts in the API

### New API contract
Every relevant historical endpoint should accept:
- `date_from`
- `date_to`

That should eventually replace or supersede the current fixed `window=all_day`
only public shape.

Expected contract evolution:

#### Rankings
Current:
- `GET /rankings?window=all_day`

Future:
- `GET /rankings?date_from=2026-02-01&date_to=2026-04-30`

#### Route summary
Current:
- `GET /routes/{route_id}/summary?window=all_day`

Future:
- `GET /routes/{route_id}/summary?date_from=...&date_to=...`

#### Map
Current:
- `GET /map/routes?window=all_day`

Future:
- `GET /map/routes?date_from=...&date_to=...`

#### Compare
Current:
- `GET /routes/compare?ids=14,49&window=all_day`

Future:
- `GET /routes/compare?ids=14,49&date_from=...&date_to=...`

### Backend validation rules
- reject missing half-ranges:
  - `date_from` without `date_to`
  - `date_to` without `date_from`
- reject `date_from > date_to`
- reject requests outside the retained daily-summary window
- optionally reject spans above a future configured max if needed

### Backend aggregation model
The API should query daily summary tables and aggregate them over the requested
range.

That means the repository layer changes from:
- `SELECT ... FROM marts.route_window_summary`

to something more like:
- `SELECT ... FROM marts.route_daily_summary WHERE service_date BETWEEN ...`
- then aggregate by `route_id`

For route detail and compare, the same rule applies:
- daily-grain source
- grouped/aggregated for the requested range

## Pipeline / dbt Design
### Core shift
The pipeline must stop treating the public serving layer as only one fully
collapsed publication snapshot.

Instead it should produce:
- **daily summary facts**
- plus any route/detail spatial support needed for those same days

### Recommended daily marts
Minimum new marts:

#### 1. `marts.route_daily_summary`
Grain:
- one row per `route_id`, `service_date`

Required fields:
- `route_id`
- `route_name`
- `route_short_name`
- `route_long_name`
- `service_date`
- `typical_trip_loss_minutes`
- `waiting_loss_minutes`
- `in_vehicle_loss_minutes`
- `matched_observed_stop_event_count`
- `resolved_unmatched_observation_count`
- `matched_headway_interval_count`
- `matched_full_trip_count`
- `metric_updated_at`

Important note:
- if route-level range aggregation must be mathematically exact, the daily table
  may need more than just already-finalized daily top-line metrics
- it may need additive or recomposable components so the API does not end up
  averaging medians incorrectly

#### 2. `marts.route_direction_daily_summary`
Grain:
- one row per `route_id`, `direction_id`, `service_date`

Needed for:
- future direction-aware public support
- direction-aware route detail
- future compare direction support

#### 3. `marts.route_hour_daily_summary`
Grain:
- one row per `route_id`, `direction_id`, `service_date`, `hour_local`

Needed to preserve:
- worst time band logic
- time-of-day story for a selected range

#### 4. `marts.route_segment_daily_metrics`
Grain:
- one row per route segment, direction, service date

Needed if route detail segment maps are expected to honor selected range rather
than showing one fixed publication-time aggregate.

#### 5. `marts.stop_wait_daily_metrics`
Grain:
- one row per stop hotspot candidate, direction, service date

Needed if stop-wait hotspots are expected to honor selected range.

### Serving-layer daily publication
From the new daily marts, build serving-ready daily relations where useful:
- `serving.route_map_daily_layer`
- `serving.route_segment_daily_layer`
- `serving.stop_wait_daily_hotspots`

These may duplicate some geometry keys for easier API querying, but they should
still stay dramatically smaller than raw/canonical history.

## Production Storage Design
### Wrong production shape for date ranges
Do not keep the entire working pipeline stack in prod if date ranges are the
goal.

That means production should not need to retain:
- raw stop observations
- raw GTFS monthly archives
- staging tables
- large canonical event tables
- large intermediate marts used only to derive daily facts

### Right production shape for date ranges
Prod should keep:
- daily summary marts / daily serving tables
- only the dimensions and geometry needed for public reads
- publication metadata

### Storage implications
The current one-month full DB is about `13.36 GiB`.

The current one-month **latest-snapshot-only serving layer** is only about
`4.76 MiB`, but that is too collapsed for real date-range exploration.

Expected daily-summary prod shape:
- much larger than `4.76 MiB`
- much smaller than `13.36 GiB`

Reasonable planning expectation:
- 1 month: tens of MB
- 3 months: tens to low hundreds of MB
- 6 months: low hundreds of MB
- all retained months: likely still under a few GB if only daily summaries and
  daily serving layers are retained

The exact size depends on whether:
- route segment daily tables are retained
- stop-wait daily tables are retained
- hour/day detail is retained
- indexes are added for interactive API reads

### Best production model
Use a split:
- build full raw/staging/canonical pipeline **outside production**
- publish only daily summary / daily serving tables **into production**

This keeps production:
- small
- queryable
- date-range capable

## Publication Flow
### Monthly update path
The monthly publication job would still operate on completed months, but the
publish result changes.

Instead of publishing:
- one fully collapsed route snapshot

it publishes:
- the daily rows for the retained historical window

### Build sequencing rule
The publication pipeline should process the retained window **one month at a
time**, not by staging a second full-size retained-window build inside
production first.

That means:
1. fetch/build one completed month
2. derive the daily summary facts for that month
3. upsert or replace that month's published daily rows in the production
   daily-summary / daily-serving tables
4. remove that month's unnecessary working-state data before moving on:
   - raw monthly ingest rows not intended for long-term prod retention
   - staging tables or transient working relations used only to derive the
     published daily facts
   - temporary publication artifacts that are not part of the retained prod
     footprint
5. move to the next month in the retained window
6. prune rows outside the retained window only after the new retained set is
   fully published

Reason:
- this keeps the production storage footprint bounded
- it avoids needing a second full retained-window build area in prod
- it matches the eventual automatic monthly refresh behavior, which naturally
  advances one completed month at a time

This rule matters especially if the product keeps:
- 3 months of daily summaries
- 6 months of daily summaries
- or later a longer retained window

The intended operational model is:
- **build incrementally in place**
- **publish one month at a time**
- **clear non-retained raw/staging/transient data after each month's publish**
- **never require production to temporarily hold two full retained windows**

### Retention behavior
If live retention is 3 months:
- keep daily summary rows only for the last 3 months
- drop older daily rows on each successful publication

If live retention is 6 months:
- keep daily summary rows only for the last 6 months
- drop older daily rows on each successful publication

### Initial bootstrap
Initial bootstrap should:
1. determine the newest completed available month
2. derive the retained window
3. build and publish one retained month at a time until the retained window is
   fully present
4. validate that the full retained daily set is present in prod
5. enable the shared date-range selector only after the daily summary dataset is
   complete and validated

## Frontend + Backend Migration Path
### Phase 1
Keep current fixed-window product behavior.

Add:
- daily marts in the pipeline
- date-range-capable backend endpoints behind a feature flag or private path

### Phase 2
Introduce the shared top-of-page date-range selector.

Update:
- homepage
- rankings
- map
- route detail

Keep compare temporarily fixed-window if needed.

### Phase 3
Add compare support using the same shared range state.

## Interaction With Direction-Level Future Work
Date ranges and direction-level public support should be designed to coexist.

That means the daily-grain marts should ideally already include:
- `direction_id`
- `direction_label`
where appropriate

Otherwise the project risks:
- doing one major public-state refactor for date range
- then doing another major public-state refactor for direction-aware public
  units

The better long-term design is:
- daily summary facts at route and route-direction grain
- route-level public serving now
- direction-level serving later without redoing the storage model from scratch

## Testing Requirements
### Pipeline
- daily summary marts build correctly for one month
- multi-month retained daily publication builds correctly
- retention pruning removes old daily rows outside the retained window

### Backend
- valid range requests return aggregated results
- out-of-window requests fail cleanly
- summary aggregation matches expected fixture totals
- route detail range queries return range-consistent segment and stop-wait data

### Frontend
- selector updates URL correctly
- selector state persists across page navigation
- homepage/rankings/map/route detail all show the same selected range
- compare preserves both selected routes and selected range

## Recommendation
If real date-range exploration is eventually important, the correct target is:

- **daily-summary production storage**
- not the current full working DB in prod
- and not a single latest published snapshot only

That architecture gives:
- real range support
- much lower prod storage than raw/canonical retention
- a clean shared selector model across the whole public site

It is the right long-term design if the product wants to feel like a real
historical exploration tool rather than a static monthly report.
