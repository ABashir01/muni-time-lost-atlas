# Title
B5 Frontend Static Bundle (Superseded By B5a/B5b)

## Goal
This document now serves as the umbrella record for the original `B5` intent. Active frontend implementation should proceed through `B5a_homepage_visual_lock` first and then `B5b_static_surface_completion`.

## Why this bundle exists
The original single frontend bundle proved too broad while the homepage visual target was still moving. Splitting the work allows the homepage to be locked first and the remaining static surfaces to be completed against a stable visual system.

## Depends on
- `B4_api_bundle`

## Active split
- `B5a_homepage_visual_lock`
  - homepage only
  - desktop-first screenshot review at `1440x900`
  - strict match against the design reference, design system, and homepage layout spec
- `B5b_static_surface_completion`
  - route detail page
  - compare view
  - map view
  - methodology page
  - shared primitives/layout finalization once the homepage is accepted

## Inputs
- fixture payloads from the API bundle
- product framing in `01_product_experience.md`
- explicit visual contract in `11_design_reference.md`
- hard visual-system rules in `12_frontend_design_system.md`
- homepage numeric layout rules in `13_homepage_layout_spec.md`

## Outputs
- a locked homepage visual direction before broader frontend completion
- a clean handoff into the remaining fixture-driven public screens

## Tests required
- see `B5a_homepage_visual_lock.md` and `B5b_static_surface_completion.md`

## Acceptance criteria
- `B5a` is accepted before broader static frontend work resumes
- `B5b` completes the remaining fixture-driven screens without regressing the locked homepage

## Non-goals
- live API integration
- realtime overlays

## Handoff to next bundle
`B6_frontend_api_integration_bundle` should start only after both `B5a` and `B5b` are accepted.

## Historical note
The earlier all-in-one `B5` implementation attempt remains useful as exploratory work, but it should not be accepted as the final frontend bundle until it has been re-evaluated through the `B5a` then `B5b` flow.
