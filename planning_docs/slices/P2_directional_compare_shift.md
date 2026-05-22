# Title
P2 Directional Compare Shift

## Goal
Make compare direction-aware after the public ranking and map surfaces have
already shifted to route-direction-level.

## Why this follow-up exists
Once homepage, rankings, and map are direction-level, compare should stop using
route-level pooled summaries too. Otherwise compare would become the remaining
public surface that still hides directional asymmetry.

## Depends on
- `P1_directional_public_shift`

## Scope
This follow-up should update:
- compare selector inputs
- compare API contract
- compare page cards and summary copy

This follow-up should not include:
- metric redesign
- realtime
- unrelated map changes

## Product behavior
- compare items should identify a specific route-direction, not just a route
- users should be able to compare:
  - two directions of different routes
  - two directions of the same route if desired
- compare cards should show:
  - route title
  - route badge
  - secondary direction/headsign line
  - direction-specific waiting/travel/total loss

## API / interface changes
The compare contract should evolve from:
- route ids only

to:
- route-direction identifiers

For MVP-like simplicity in a GET flow, prefer a URL-safe encoded identifier
format unless later API redesign justifies a richer request body.

The compare contract should explicitly support:
- preserving requested order
- distinguishing two directions of the same route

## Acceptance criteria
- compare selector shows direction-specific options
- compare cards display direction labels clearly
- compare results are direction-specific, not pooled route-level summaries
- the compare page stays consistent with the direction-level public ranking unit

## Test cases and scenarios
- compare can accept two route-directions from different routes
- compare can accept two directions from the same route
- order is preserved in the response and UI
- direction labels remain readable and not ambiguous in the card layout

## Non-goals
- route-level ranking behavior
- citywide map changes
- realtime
