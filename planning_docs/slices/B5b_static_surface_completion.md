# Title
B5b Static Surface Completion

## Goal
Finish the remaining public-facing static frontend surfaces against fixtures after the homepage design is locked.

## Why this bundle exists
Once the homepage visual system is stable, the rest of the frontend can be completed with less churn and less risk of dragging unresolved homepage design decisions across every screen.

## Depends on
- `B4_api_bundle`
- `B4a_stop_wait_api_extension`
- accepted `B5a_homepage_visual_lock`

## Touches
- route detail page
- compare view
- map view
- methodology page
- shared layout/design primitives, as needed

## Inputs
- fixture payloads from the API bundle and stop-wait extension
- accepted homepage design direction from `B5a`
- design docs:
  - `11_design_reference.md`
  - `12_frontend_design_system.md`

## Outputs
- complete static frontend MVP against fixtures
- no live backend dependency for functional or design review

## Implementation notes
- preserve the locked homepage without reopening its composition
- complete route detail, compare, map, and methodology surfaces
- keep the public language consistent with the API and methodology docs
- keep the static app reviewable without live backend coupling
- prefer finishing coherent public screens over adding extra optional UI states

## Tests required
- one primary frontend render/test suite covering the major remaining screens against fixtures
- one smoke-level pass for the main product surfaces

## Acceptance criteria
- route detail, compare, map, and methodology pages render from fixtures
- the product hierarchy and core metric language read correctly
- the accepted homepage remains intact
- the bundle is reviewable without live backend coupling

## Non-goals
- live API integration
- realtime overlays

## Handoff to next bundle
`B6_frontend_api_integration_bundle` should replace fixtures with live API responses while preserving the accepted static UI.
