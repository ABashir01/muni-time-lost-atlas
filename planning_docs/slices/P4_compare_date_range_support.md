# Title
P4 Compare Date-Range Support

## Goal
Finish compare-specific date-range behavior after the broader public
date-range model already exists across homepage, rankings, map, and route
detail.

## Why this follow-up exists
Compare is likely the most awkward public surface to retrofit for range support
because it needs to preserve both:
- multiple selected routes
- one shared selected historical range

If the main date-range work lands first, compare can be handled as a smaller,
deliberate follow-on rather than forcing all of that complexity into the first
range-support pass.

## Depends on
- `P3_public_date_range_support`

## Scope
This follow-up should update:
- compare request shape
- compare deep-link behavior
- compare cards and supporting copy

This follow-up should not include:
- realtime
- new metric families
- unrelated map or homepage redesign

## Product behavior
- compare should use the same shared selected historical range as the rest of
  the public product
- compare should preserve both:
  - the selected range
  - the requested route or route-direction items in order
- compare should not introduce a separate, competing date-range selector if the
  rest of the product already exposes one shared range model

## API / interface changes
Expected future changes:
- compare should accept explicit historical range parameters rather than only
  the fixed published window
- compare links should preserve selected items and selected range together
- if route-direction public support exists by then, compare should remain
  compatible with that direction-aware identifier model

## Acceptance criteria
- compare results reflect the same selected range used on other public surfaces
- compare links remain shareable and reproducible
- selected route order is preserved
- compare remains visually legible after range-aware copy is added

## Test cases and scenarios
- compare accepts two to four items plus one selected range
- compare preserves requested order while applying the shared range
- links copied from compare reopen the same routes and the same range
- compare stays consistent with any already-implemented direction-aware public
  unit

## Non-goals
- homepage range UX
- full rankings range UX
- full map range UX
- realtime
