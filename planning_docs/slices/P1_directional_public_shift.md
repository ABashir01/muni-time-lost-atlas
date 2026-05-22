# Title
P1 Directional Public Shift

## Goal
Move the public ranking and map unit from route-level to route-direction-level
everywhere public.

## Why this follow-up exists
The current MVP public experience still ranks and maps routes at the route
level, even though the database already exposes direction-level differences in
`marts.route_direction_summary`.

That means the current public surface can materially understate what riders
experience on routes whose two directions diverge sharply. This is documented
explicitly in methodology for the MVP, but the long-term public product should
stop pooling those directions together.

## Depends on
- current historical/static MVP being complete
- direction-level metrics continuing to exist in:
  - `marts.route_direction_summary`
  - `marts.route_hour_summary`
  - route-detail directional segment and stop-wait layers

## Public unit change
Change the public ranking unit from:
- `route_id`

to:
- `route_id + direction_id`

Use the existing `direction_label` / headsign text already materialized in the
database.

## Scope
This follow-up should update:
- homepage ranking cards
- homepage highlighted map features
- full rankings surface
- full map view
- route-detail entry behavior when launched from a ranked public item

This follow-up should not yet include:
- compare
- realtime
- metric redesign

## Product behavior
### Homepage
- cards rank route-directions, not pooled routes
- the main card title remains the route identity, such as `22 Fillmore`
- add a secondary line for the direction/headsign, such as `Bay Street`
- the displayed loss number is the direction-specific value
- clicking a card should open route detail focused on that same direction

### Rankings
- the rankings surface should list direction-specific entries
- if two directions of the same route are both high-loss, both may appear
- rank order should be based on the selected direction-level metric

### Map
- the full public map should also become direction-level so the public unit
  stays consistent across homepage, rankings, and map
- do not mix route-level homepage/map results with direction-level rankings

### Route detail
- route detail should open directly to the clicked direction when entered from
  a public direction-ranked item
- route-level overview may still exist as a secondary concept, but not as the
  primary public ranking unit

## API / data contract changes
Expected future changes:
- `/rankings` should support a direction-aware public mode
- `/map/routes` should publish direction-level features rather than one pooled
  route-level feature per route
- the route map feature properties should include:
  - `direction_id`
  - `direction_label`
- route-detail entry links should carry direction explicitly

## Cartographic strategy
The direction-level citywide map will require an intentional rendering strategy.

The implementation should explicitly handle:
- overlapping inbound/outbound geometries
- hover-first labeling instead of labeling every feature at once
- render ordering by severity or selected state
- line styling or casing that helps distinguish overlapping directions without
  destroying readability

The goal is not to create a full transit operations console. The goal is to
keep the public product editorial and readable while making the public unit
truthful.

## Acceptance criteria
- a route like `SF:22` can appear as two separate public ranking entries
- homepage card and homepage highlighted map refer to the same
  direction-specific unit
- full map uses direction-level published features
- clicking a ranked item opens route detail on that same direction
- public docs no longer need to defend route-level pooling as the main overview

## Test cases and scenarios
- route-directions with materially different losses rank separately
- two directions of the same route can both appear in the top rankings
- direction-specific card labels are rider-facing and readable
- map hover/selection identifies both route and direction
- route detail loads the clicked direction by default

## Non-goals
- compare
- realtime overlays
- passenger-weighted metric changes
- major visual redesign
