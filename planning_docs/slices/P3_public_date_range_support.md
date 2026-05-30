# Title
P3 Public Date-Range Support

## Goal
Add shared public historical date-range support across the major public product
surfaces without turning the site into a raw analytics dashboard.

## Why this follow-up exists
The current MVP product is published from one rolling historical window and
does not yet support user-selected historical ranges.

That is acceptable for MVP, but the long-term product should let a user choose
and carry one historical range across the whole public experience rather than
showing only a single published window forever.

## Depends on
- the rolling historical publication path being stable
- the public historical/static product already working coherently from the live
  rolling window
- the current MVP docs continuing to disclose that date-range support is
  deferred

## Scope
This follow-up should update:
- homepage
- rankings
- map
- route detail
- shared navigation and deep-link behavior for the selected range
- supporting API contracts and summary marts

This follow-up should not yet include:
- compare-specific final behavior if that work is easier to execute separately
- realtime
- passenger-weighted metric redesign

## Product behavior
### Shared range model
- use one shared selected historical range across the public experience
- preserve that range through navigation rather than giving every page its own
  unrelated selector
- keep the first-load experience editorial by defaulting to a strong preset or
  the full live window

### Range UX
- support both:
  - presets
  - explicit custom start and end dates
- keep all public date choices bounded to the retained rolling live window
- avoid dashboard-like per-widget controls

### Public surfaces
- homepage rankings, map highlight, and explanatory copy should reflect the
  selected range
- full rankings should rank using the same selected range
- full map should render using the same selected range
- route detail should inherit and preserve the selected range

## Architecture direction
- future implementation should use daily-grain summary marts
- API endpoints should aggregate those daily summaries for the selected range
- do not recompute public historical ranges directly from raw stop observations
  or other low-level event tables per request

Expected future daily-grain support should cover at least:
- route-level summary aggregation
- direction-level summary aggregation where applicable
- route-detail-supporting summaries needed to keep route detail consistent with
  the selected range

## API / interface changes
Expected future changes:
- public historical endpoints should evolve from the current fixed-window model
  to a shared range-aware contract
- prefer explicit range parameters such as:
  - `date_from`
  - `date_to`
- preset identifiers may exist in the frontend, but the backend should resolve
  requests to explicit date bounds

## Acceptance criteria
- one selected range updates homepage, rankings, map, and route detail
- navigation preserves the selected range
- out-of-window requests fail cleanly
- no public range query requires raw-event recomputation
- the site still feels editorial rather than dashboard-like

## Test cases and scenarios
- selecting a preset updates all supported overview surfaces consistently
- selecting a custom range inside the live window updates those surfaces
  consistently
- route detail preserves the shared range when opened from a ranked or mapped
  item
- range validation rejects requests outside the retained live window
- API range queries read daily summaries rather than raw historical event
  tables

## Non-goals
- compare-specific implementation details if compare remains a later follow-on
- realtime
- major redesign of the homepage or map presentation

## Companion implementation sketch
See also:
- [P3a_real_date_range_architecture.md](./P3a_real_date_range_architecture.md)
